import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import Document, DocumentAccess, DocumentCategory, DocumentTemplate
from .forms import DocumentUploadForm, DocumentVersionForm, DocumentSearchForm, DocumentApprovalForm
from apps.referrals.models import Referral
from utils.notion.client import NotionService
from utils.notion.documents import create_document_in_notion, update_document_in_notion
from django.conf import settings


@login_required
def document_list(request):
    """List all documents with search and filtering."""
    form = DocumentSearchForm(request.GET)
    documents = Document.objects.all()
    
    # Filter by search query
    if request.GET.get('query'):
        query = request.GET.get('query')
        documents = documents.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        )
    
    # Filter by category
    if request.GET.get('category'):
        documents = documents.filter(category_id=request.GET.get('category'))
    
    # Filter by status
    if request.GET.get('status'):
        documents = documents.filter(status=request.GET.get('status'))
    
    # Filter by file type
    if request.GET.get('file_type'):
        file_type = request.GET.get('file_type')
        if file_type == 'pdf':
            documents = documents.filter(file_type='pdf')
        elif file_type == 'doc':
            documents = documents.filter(file_type__in=['doc', 'docx'])
        elif file_type == 'image':
            documents = documents.filter(file_type__in=['jpg', 'jpeg', 'png', 'gif'])
        elif file_type == 'excel':
            documents = documents.filter(file_type__in=['xls', 'xlsx'])
    
    # Order by created date
    documents = documents.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'documents': page_obj,
        'total_count': documents.count(),
    }
    return render(request, 'documents/document_list.html', context)


@login_required
def document_upload(request):
    """Upload a new document."""
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            
            # Create in Notion
            try:
                notion_service = NotionService()
                database_id = settings.NOTION_DOCUMENT_DATABASE
                result = create_document_in_notion(document, notion_service, database_id)
                document.notion_id = result['id']
                document.save()
            except Exception as e:
                messages.warning(request, f'Document saved locally but Notion sync failed: {str(e)}')
            
            # Log access
            DocumentAccess.objects.create(
                document=document,
                user=request.user,
                action='edit',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'Document uploaded successfully!')
            return redirect('documents:document_detail', pk=document.pk)
    else:
        form = DocumentUploadForm()
    
    context = {
        'form': form,
        'action': 'Upload',
    }
    return render(request, 'documents/document_form.html', context)


@login_required
def document_detail(request, pk):
    """View document details."""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permissions
    if not document.is_public and document.uploaded_by != request.user and not request.user.is_staff:
        raise Http404("Document not found")
    
    # Log access
    DocumentAccess.objects.create(
        document=document,
        user=request.user,
        action='view',
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Get version history
    versions = Document.objects.filter(
        Q(parent_document=document) | Q(pk=document.pk)
    ).order_by('-version')
    
    # Get access logs
    access_logs = document.access_logs.select_related('user')[:10]
    
    context = {
        'document': document,
        'versions': versions,
        'access_logs': access_logs,
    }
    return render(request, 'documents/document_detail.html', context)


@login_required
def document_download(request, pk):
    """Download a document."""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permissions
    if not document.is_public and document.uploaded_by != request.user and not request.user.is_staff:
        raise Http404("Document not found")
    
    # Log access
    DocumentAccess.objects.create(
        document=document,
        user=request.user,
        action='download',
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Serve file
    if document.file:
        file_path = document.file.path
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/octet-stream")
                response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_path)}'
                return response
    
    raise Http404("File not found")


@login_required
def document_new_version(request, pk):
    """Upload a new version of a document."""
    document = get_object_or_404(Document, pk=pk)
    
    # Check permissions
    if document.uploaded_by != request.user and not request.user.is_staff:
        raise Http404("Document not found")
    
    if request.method == 'POST':
        form = DocumentVersionForm(request.POST, request.FILES)
        if form.is_valid():
            # Create new version
            new_version = document.create_new_version(form.cleaned_data['file'])
            new_version.uploaded_by = request.user
            
            if form.cleaned_data['description']:
                new_version.description = form.cleaned_data['description']
            
            new_version.save()
            
            # Sync with Notion
            try:
                notion_service = NotionService()
                database_id = settings.NOTION_DOCUMENT_DATABASE
                result = create_document_in_notion(new_version, notion_service, database_id)
                new_version.notion_id = result['id']
                new_version.save()
            except Exception as e:
                messages.warning(request, f'New version saved but Notion sync failed: {str(e)}')
            
            # Log access
            DocumentAccess.objects.create(
                document=new_version,
                user=request.user,
                action='edit',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'New version {new_version.version} uploaded successfully!')
            return redirect('documents:document_detail', pk=new_version.pk)
    else:
        form = DocumentVersionForm()
    
    context = {
        'form': form,
        'document': document,
    }
    return render(request, 'documents/document_version_form.html', context)


@login_required
def document_approve_reject(request, pk):
    """Approve or reject a document."""
    if not request.user.is_staff:
        raise Http404("Page not found")
    
    document = get_object_or_404(Document, pk=pk)
    
    if request.method == 'POST':
        form = DocumentApprovalForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            comments = form.cleaned_data.get('comments', '')
            
            # Update status
            document.status = 'approved' if action == 'approve' else 'rejected'
            document.save()
            
            # Update in Notion
            try:
                notion_service = NotionService()
                update_document_in_notion(document, notion_service)
            except Exception as e:
                messages.warning(request, f'Status updated but Notion sync failed: {str(e)}')
            
            # Log access
            DocumentAccess.objects.create(
                document=document,
                user=request.user,
                action=action,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'Document {action}d successfully!')
            return redirect('documents:document_detail', pk=document.pk)
    else:
        form = DocumentApprovalForm()
    
    context = {
        'form': form,
        'document': document,
    }
    return render(request, 'documents/document_approval_form.html', context)


@login_required
def template_list(request):
    """List document templates."""
    templates = DocumentTemplate.objects.filter(is_active=True)
    
    # Filter by category
    if request.GET.get('category'):
        templates = templates.filter(category_id=request.GET.get('category'))
    
    templates = templates.order_by('category', 'name')
    
    context = {
        'templates': templates,
        'categories': DocumentCategory.objects.all(),
    }
    return render(request, 'documents/template_list.html', context)


@login_required
def template_download(request, pk):
    """Download a document template."""
    template = get_object_or_404(DocumentTemplate, pk=pk, is_active=True)
    
    if template.file:
        file_path = template.file.path
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/octet-stream")
                response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_path)}'
                return response
    
    raise Http404("File not found")


# API endpoints for AJAX requests
@login_required
def document_search_api(request):
    """API endpoint for document search."""
    query = request.GET.get('q', '')
    documents = Document.objects.filter(
        Q(title__icontains=query) | 
        Q(description__icontains=query) |
        Q(tags__icontains=query)
    )[:10]
    
    results = []
    for doc in documents:
        results.append({
            'id': str(doc.id),
            'title': doc.title,
            'description': doc.description[:100],
            'file_type': doc.file_type,
            'url': doc.get_absolute_url() if hasattr(doc, 'get_absolute_url') else f'/documents/{doc.id}/',
        })
    
    return JsonResponse({'results': results})