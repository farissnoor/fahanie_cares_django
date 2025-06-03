"""
Admin views for Ministry Program management.
Provides CRUD interface for authorized users.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from decimal import Decimal
import json

from .models import MinistryProgram, MinistryProgramHistory
from .permissions import MinistryProgramPermissions
from .forms import MinistryProgramForm, ProgramSearchForm, ImportProgramsForm # Import ProgramSearchForm and ImportProgramsForm
from .audit import MinistryProgramAuditService
from .bulk_operations import MinistryProgramBulkOperations


@method_decorator(login_required, name='dispatch')
class AdminDashboardView(TemplateView):
    """Main admin dashboard for ministry programs."""
    template_name = 'services/admin/dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user has admin permissions
        if not request.user.user_type in ['mp', 'staff']:
            messages.error(request, 'You do not have permission to access the admin dashboard.')
            return redirect('ministries_ppas')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialize filter form
        filter_form = ProgramSearchForm(self.request.GET)
        context['filter_form'] = filter_form

        # Get user's accessible programs
        user_ministries = MinistryProgramPermissions.get_user_ministry_permissions(self.request.user)
        
        if self.request.user.user_type in ['mp', 'staff']:
            programs = MinistryProgram.objects.filter(is_deleted=False)
        else:
            programs = MinistryProgram.objects.filter(
                ministry__in=user_ministries,
                is_deleted=False
            )
        
        # Apply filters from form
        if filter_form.is_valid():
            ministry_filter = filter_form.cleaned_data.get('ministry')
            status_filter = filter_form.cleaned_data.get('status')
            search_query = filter_form.cleaned_data.get('search_query')
            priority_level = filter_form.cleaned_data.get('priority_level')
            budget_min = filter_form.cleaned_data.get('budget_min')
            budget_max = filter_form.cleaned_data.get('budget_max')
            is_featured = filter_form.cleaned_data.get('is_featured')

            if ministry_filter:
                programs = programs.filter(ministry=ministry_filter)
            if status_filter:
                programs = programs.filter(status=status_filter)
            if search_query:
                programs = programs.filter(
                    Q(title__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(code__icontains=search_query)
                )
            if priority_level:
                programs = programs.filter(priority_level=priority_level)
            if budget_min:
                programs = programs.filter(total_budget__gte=budget_min)
            if budget_max:
                programs = programs.filter(total_budget__lte=budget_max)
            if is_featured:
                programs = programs.filter(is_featured=True)

        # Dashboard statistics
        context['total_programs'] = programs.count()
        context['active_programs'] = programs.filter(status='active').count()
        context['pending_programs'] = programs.filter(status='pending_approval').count()
        context['draft_programs'] = programs.filter(status='draft').count()
        
        # Budget summary
        budget_stats = programs.aggregate(
            total_budget=Sum('total_budget'),
            allocated_budget=Sum('allocated_budget'),
            utilized_budget=Sum('utilized_budget')
        )
        context.update(budget_stats)
        
        # Ministry breakdown
        ministry_stats = []
        total_budget_all_ministries = budget_stats['total_budget'] or Decimal('0')
        
        # Define a list of colors for progress bars
        progress_bar_colors = ['primary', 'success', 'info', 'warning', 'danger', 'secondary', 'dark']
        color_index = 0

        for ministry_code, ministry_name in MinistryProgram.MINISTRIES:
            if not user_ministries or ministry_code in user_ministries:
                ministry_programs = programs.filter(ministry=ministry_code)
                count = ministry_programs.count()
                if count > 0:
                    budget = ministry_programs.aggregate(
                        total=Sum('total_budget')
                    )['total'] or Decimal('0')
                    
                    percentage = (budget / total_budget_all_ministries * 100) if total_budget_all_ministries > 0 else 0
                    
                    ministry_stats.append({
                        'code': ministry_code,
                        'name': ministry_name,
                        'count': count,
                        'budget': budget,
                        'percentage': percentage,
                        'color': progress_bar_colors[color_index % len(progress_bar_colors)]
                    })
                    color_index += 1
        
        context['ministry_stats'] = ministry_stats
        
        # Recent activity
        recent_history = MinistryProgramHistory.objects.filter(
            program__in=programs
        ).select_related('program', 'changed_by').order_by('-changed_at')[:10]
        
        # Format recent activity for display
        formatted_recent_activity = []
        for activity in recent_history:
            changes_str = ""
            if activity.changed_fields:
                changes_list = []
                for field, new_val in activity.new_values.items():
                    old_val = activity.old_values.get(field, 'N/A')
                    changes_list.append(f"{field}: '{old_val}' -> '{new_val}'")
                changes_str = "; ".join(changes_list)

            formatted_recent_activity.append({
                'program_title': activity.program.title,
                'action': activity.action_type,
                'user': activity.changed_by.get_full_name() if activity.changed_by else 'System',
                'timestamp': activity.changed_at,
                'changes': changes_str,
            })
        context['recent_activity'] = formatted_recent_activity
        
        # Featured programs (for dashboard display)
        featured_programs = programs.filter(
            status='active'
        ).order_by('-allocated_budget')[:5]  # Top 5 by allocated budget
        context['featured_programs'] = featured_programs
        
        # Define a list of colors for progress bars (re-using for consistency)
        progress_bar_colors = ['primary', 'success', 'info', 'warning', 'danger', 'secondary', 'dark', 'primary'] # Added one more color to avoid index out of bounds

        # Additional dashboard stats
        total_programs_count = programs.count()
        total_budget_sum = budget_stats['total_budget'] or Decimal('0')
        allocated_budget_sum = budget_stats['allocated_budget'] or Decimal('0')
        utilized_budget_sum = budget_stats['utilized_budget'] or Decimal('0')

        context['stats'] = {
            'total_programs': total_programs_count,
            'active_programs': programs.filter(status='active').count(),
            'pending_programs': programs.filter(status='pending_approval').count(),
            'draft_programs': programs.filter(status='draft').count(),
            'total_budget': total_budget_sum,
            'allocated_budget': allocated_budget_sum,
            'utilized_budget': utilized_budget_sum,
            'programs_this_month': programs.filter(
                created_at__month=timezone.now().month
            ).count(),
            'completed_programs': programs.filter(status='completed').count(),
            'avg_budget': (total_budget_sum / max(total_programs_count, 1)) if total_programs_count > 0 else Decimal('0'),
            'total_beneficiaries': programs.aggregate(
                total=Sum('estimated_beneficiaries')
            )['total'] or 0,
            'high_priority': programs.filter(priority_level='high').count(),
            'budget_utilization_percentage': (utilized_budget_sum / allocated_budget_sum * 100) if allocated_budget_sum > 0 else 0,
        }

        # Programs by PPA Type
        ppa_type_stats = []
        ppa_color_index = 0
        for ppa_code, ppa_name in MinistryProgram.PPA_TYPES:
            ppa_programs = programs.filter(ppa_type=ppa_code)
            count = ppa_programs.count()
            if count > 0:
                percentage = (count / total_programs_count * 100) if total_programs_count > 0 else 0
                ppa_type_stats.append({
                    'code': ppa_code,
                    'name': ppa_name,
                    'count': count,
                    'percentage': percentage,
                    'color': progress_bar_colors[ppa_color_index % len(progress_bar_colors)]
                })
                ppa_color_index += 1
        context['ppa_type_stats'] = ppa_type_stats

        # Program Status Distribution
        status_stats = []
        status_color_index = 0
        for status_code, status_name in MinistryProgram.STATUS_CHOICES:
            status_programs = programs.filter(status=status_code)
            count = status_programs.count()
            if count > 0:
                percentage = (count / total_programs_count * 100) if total_programs_count > 0 else 0
                status_stats.append({
                    'code': status_code,
                    'name': status_name,
                    'count': count,
                    'percentage': percentage,
                    'color': progress_bar_colors[status_color_index % len(progress_bar_colors)]
                })
                status_color_index += 1
        context['status_stats'] = status_stats

        # Program Priority Distribution
        priority_stats = []
        priority_color_index = 0
        for priority_code, priority_name in MinistryProgram.PRIORITY_LEVELS: # Assuming PRIORITY_LEVELS exists in MinistryProgram
            priority_programs = programs.filter(priority_level=priority_code)
            count = priority_programs.count()
            if count > 0:
                percentage = (count / total_programs_count * 100) if total_programs_count > 0 else 0
                priority_stats.append({
                    'code': priority_code,
                    'name': priority_name,
                    'count': count,
                    'percentage': percentage,
                    'color': progress_bar_colors[priority_color_index % len(progress_bar_colors)]
                })
                priority_color_index += 1
        context['priority_stats'] = priority_stats
        
        # User permissions
        context['user_ministries'] = user_ministries
        context['can_export'] = MinistryProgramPermissions.can_export_programs(self.request.user)
        
        return context


@method_decorator(login_required, name='dispatch')
class ProgramListView(TemplateView):
    """List and manage ministry programs."""
    template_name = 'services/admin/program_list.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.user_type in ['mp', 'staff', 'coordinator']:
            messages.error(request, 'You do not have permission to manage programs.')
            return redirect('ministries_ppas')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's accessible programs
        user_ministries = MinistryProgramPermissions.get_user_ministry_permissions(self.request.user)
        
        if self.request.user.user_type in ['mp', 'staff']:
            programs = MinistryProgram.objects.filter(is_deleted=False)
        else:
            programs = MinistryProgram.objects.filter(
                ministry__in=user_ministries,
                is_deleted=False
            )
        
        # Apply filters
        ministry_filter = self.request.GET.get('ministry')
        status_filter = self.request.GET.get('status')
        search_query = self.request.GET.get('search')
        
        if ministry_filter:
            programs = programs.filter(ministry=ministry_filter)
        
        if status_filter:
            programs = programs.filter(status=status_filter)
        
        if search_query:
            programs = programs.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(code__icontains=search_query)
            )
        
        # Pagination
        paginator = Paginator(programs.order_by('-created_at'), 20)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context.update({
            'programs': page_obj,
            'user_ministries': user_ministries,
            'ministry_filter': ministry_filter,
            'status_filter': status_filter,
            'search_query': search_query,
            'total_programs': programs.count(),
            'can_create': MinistryProgramPermissions.can_create_program(self.request.user),
            'can_export': MinistryProgramPermissions.can_export_programs(self.request.user),
        })
        
        return context


@method_decorator(login_required, name='dispatch')
class ProgramCreateView(CreateView):
    """Create new ministry program."""
    model = MinistryProgram
    form_class = MinistryProgramForm
    template_name = 'services/admin/program_form.html'
    success_url = reverse_lazy('admin_program_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not MinistryProgramPermissions.can_create_program(request.user):
            messages.error(request, 'You do not have permission to create programs.')
            return redirect('admin_program_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.last_modified_by = self.request.user
        
        # Check ministry permissions
        ministry = form.cleaned_data['ministry']
        if not MinistryProgramPermissions.can_create_program(self.request.user, ministry):
            messages.error(self.request, f'You do not have permission to create programs for {ministry}.')
            return self.form_invalid(form)
        
        response = super().form_valid(form)
        
        # Create audit trail
        MinistryProgramAuditService.log_program_action(
            program=self.object,
            action_type='create',
            user=self.request.user,
            request=self.request,
            reason='New program created via admin interface'
        )
        
        messages.success(self.request, f'Program "{self.object.title}" created successfully.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Program'
        context['user_ministries'] = MinistryProgramPermissions.get_user_ministry_permissions(self.request.user)
        return context


@method_decorator(login_required, name='dispatch')
class ProgramUpdateView(UpdateView):
    """Update existing ministry program."""
    model = MinistryProgram
    form_class = MinistryProgramForm
    template_name = 'services/admin/program_form.html'
    success_url = reverse_lazy('admin_program_list')
    
    def dispatch(self, request, *args, **kwargs):
        program = self.get_object()
        if not MinistryProgramPermissions.can_edit_program(request.user, program):
            messages.error(request, 'You do not have permission to edit this program.')
            return redirect('admin_program_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Track changes for audit
        old_values = {}
        new_values = {}
        changed_fields = []
        
        for field_name in form.changed_data:
            old_values[field_name] = str(getattr(self.object, field_name, ''))
            new_values[field_name] = str(form.cleaned_data[field_name])
            changed_fields.append(field_name)
        
        form.instance.last_modified_by = self.request.user
        response = super().form_valid(form)
        
        # Create audit trail if changes were made
        if changed_fields:
            MinistryProgramAuditService.log_program_action(
                program=self.object,
                action_type='update',
                user=self.request.user,
                request=self.request,
                reason='Program updated via admin interface',
                changed_fields=changed_fields,
                old_values=old_values,
                new_values=new_values
            )
        
        messages.success(self.request, f'Program "{self.object.title}" updated successfully.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Program: {self.object.title}'
        context['user_ministries'] = MinistryProgramPermissions.get_user_ministry_permissions(self.request.user)
        return context


@login_required
def program_detail_view(request, pk):
    """View program details with edit/delete options."""
    program = get_object_or_404(MinistryProgram, pk=pk, is_deleted=False)
    
    # Check view permissions
    if not MinistryProgramPermissions.can_view_program(request.user, program):
        messages.error(request, 'You do not have permission to view this program.')
        return redirect('admin_program_list')
    
    # Get program history if user has permission
    history = []
    if MinistryProgramPermissions.can_view_history(request.user, program):
        history = MinistryProgramHistory.objects.filter(
            program=program
        ).select_related('changed_by').order_by('-changed_at')[:20]
    
    context = {
        'program': program,
        'history': history,
        'can_edit': MinistryProgramPermissions.can_edit_program(request.user, program),
        'can_delete': MinistryProgramPermissions.can_delete_program(request.user, program),
        'can_approve': MinistryProgramPermissions.can_approve_program(request.user, program),
        'can_view_history': MinistryProgramPermissions.can_view_history(request.user, program),
    }
    
    return render(request, 'services/admin/program_detail.html', context)


@login_required
def program_delete_view(request, pk):
    """Soft delete a program."""
    program = get_object_or_404(MinistryProgram, pk=pk, is_deleted=False)
    
    # Check permissions
    if not MinistryProgramPermissions.can_delete_program(request.user, program):
        messages.error(request, 'You do not have permission to delete this program.')
        return redirect('program_list')
    
    if request.method == 'POST':
        reason = request.POST.get('reason', 'Deleted via admin interface')
        program.soft_delete(request.user, reason)
        
        # Create audit trail
        MinistryProgramAuditService.log_program_action(
            program=program,
            action_type='delete',
            user=request.user,
            request=request,
            reason=reason
        )
        
        messages.success(request, f'Program "{program.title}" has been deleted.')
        return redirect('program_list')
    
    return render(request, 'services/admin/program_delete_confirm.html', {
        'program': program
    })


@login_required
def program_approve_view(request, pk):
    """Approve a program."""
    program = get_object_or_404(MinistryProgram, pk=pk, is_deleted=False)
    
    if not MinistryProgramPermissions.can_approve_program(request.user, program):
        messages.error(request, 'You do not have permission to approve this program.')
        return redirect('admin_program_list')
    
    if request.method == 'POST':
        program.approve(request.user)
        
        # Create audit trail
        MinistryProgramAuditService.log_program_action(
            program=program,
            action_type='approve',
            user=request.user,
            request=request,
            reason='Program approved via admin interface'
        )
        
        messages.success(request, f'Program "{program.title}" has been approved.')
        return redirect('admin_program_detail', pk=pk)
    
    return render(request, 'services/admin/program_approve_confirm.html', {
        'program': program
    })


@login_required
def export_programs_view(request):
    """Export programs to various formats."""
    # Check permissions
    if not MinistryProgramPermissions.can_export_programs(request.user):
        messages.error(request, 'You do not have permission to export programs.')
        return redirect('program_list')
    
    if request.method == 'POST':
        export_format = request.POST.get('format', 'csv')
        ministry = request.POST.get('ministry', '')
        status = request.POST.get('status', '')
        
        try:
            content, content_type, filename = MinistryProgramBulkOperations.export_programs(
                file_format=export_format,
                user=request.user,
                ministry=ministry if ministry else None,
                status=status if status else None
            )
            
            response = HttpResponse(content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            messages.error(request, f'Export failed: {str(e)}')
            return redirect('admin_program_list')
    
    # Get filter options
    user_ministries = MinistryProgramPermissions.get_user_ministry_permissions(request.user)
    
    context = {
        'user_ministries': user_ministries,
        'status_choices': MinistryProgram.STATUS_CHOICES,
    }
    
    return render(request, 'services/admin/export_programs.html', context)


@login_required
def import_programs_view(request):
    """Import programs from various formats."""
    if not MinistryProgramPermissions.can_export_programs(request.user): # Assuming import permission is tied to export for now
        messages.error(request, 'You do not have permission to import programs.')
        return redirect('program_list')

    if request.method == 'POST':
        form = ImportProgramsForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            overwrite_existing = form.cleaned_data['overwrite_existing']
            validate_only = form.cleaned_data['validate_only']

            file_name = uploaded_file.name
            if file_name.endswith('.csv'):
                file_format = 'csv'
            elif file_name.endswith('.json'):
                file_format = 'json'
            elif file_name.endswith('.xlsx') or file_name.endswith('.xls'):
                messages.error(request, 'Excel import is not yet supported. Please use CSV or JSON.')
                return redirect('program_import')
            else:
                messages.error(request, 'Unsupported file type. Please upload a CSV or JSON file.')
                return redirect('program_import')

            try:
                # Read file content
                file_content = uploaded_file.read()
                
                # Perform import operation
                results = MinistryProgramBulkOperations.import_programs(
                    file_content=file_content,
                    file_format=file_format,
                    user=request.user,
                    update_existing=overwrite_existing,
                    dry_run=validate_only
                )

                if results['success']:
                    if validate_only:
                        messages.success(request, f"File validated successfully. {results['created']} new programs, {results['updated']} updated programs, {results['skipped']} skipped programs.")
                    else:
                        messages.success(request, f"Import successful! {results['created']} programs created, {results['updated']} updated.")
                else:
                    messages.error(request, "Import failed. Please check errors below.")
                
                for error in results['errors']:
                    messages.error(request, f"Import Error: {error}")
                for warning in results['warnings']:
                    messages.warning(request, f"Import Warning: {warning}")

                context = {
                    'form': form,
                    'user_ministries': MinistryProgramPermissions.get_user_ministry_permissions(request.user),
                    'import_results': results # Pass results to template for detailed display
                }
                return render(request, 'services/admin/import_programs.html', context)

            except Exception as e:
                messages.error(request, f"An unexpected error occurred during import: {str(e)}")
                return redirect('program_import')
        else:
            # Form is not valid, re-render with errors
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ImportProgramsForm()

    context = {
        'form': form,
        'user_ministries': MinistryProgramPermissions.get_user_ministry_permissions(request.user),
    }
    return render(request, 'services/admin/import_programs.html', context)


@login_required
def bulk_actions_view(request):
    """Handle bulk actions on programs."""
    if request.method == 'POST':
        action = request.POST.get('action')
        program_ids = request.POST.getlist('program_ids')
        
        if not program_ids:
            messages.error(request, 'No programs selected.')
            return redirect('admin_program_list')
        
        programs = MinistryProgram.objects.filter(
            id__in=program_ids,
            is_deleted=False
        )
        
        # Check permissions for each program
        authorized_programs = []
        for program in programs:
            if action == 'delete' and MinistryProgramPermissions.can_delete_program(request.user, program):
                authorized_programs.append(program)
            elif action in ['approve', 'activate'] and MinistryProgramPermissions.can_approve_program(request.user, program):
                authorized_programs.append(program)
            elif MinistryProgramPermissions.can_edit_program(request.user, program):
                authorized_programs.append(program)
        
        count = 0
        for program in authorized_programs:
            if action == 'delete':
                reason = request.POST.get('reason', 'Bulk deletion via admin interface')
                program.soft_delete(request.user, reason)
                count += 1
            elif action == 'approve':
                program.approve(request.user)
                count += 1
            elif action == 'activate':
                program.status = 'active'
                program.last_modified_by = request.user
                program.save()
                count += 1
            elif action == 'suspend':
                program.status = 'suspended'
                program.last_modified_by = request.user
                program.save()
                count += 1
        
        messages.success(request, f'{action.title()} applied to {count} programs.')
        return redirect('program_list')
    
    return redirect('program_list')


@login_required
def program_history_view(request):
    """View all program activity history."""
    # Check if user has permission to view program history
    if not request.user.user_type in ['mp', 'staff']:
        messages.error(request, 'You do not have permission to view program history.')
        return redirect('ministries_ppas')
    
    # Get filter parameters
    program_id = request.GET.get('program')
    action_type = request.GET.get('action')
    user_id = request.GET.get('user')
    
    # Base queryset
    history_queryset = MinistryProgramHistory.objects.select_related(
        'program', 'changed_by'
    ).order_by('-changed_at')
    
    # Apply filters
    if program_id:
        history_queryset = history_queryset.filter(program_id=program_id)
    
    if action_type:
        history_queryset = history_queryset.filter(action=action_type)
    
    if user_id:
        history_queryset = history_queryset.filter(changed_by_id=user_id)
    
    # Pagination
    paginator = Paginator(history_queryset, 25)
    page_number = request.GET.get('page')
    history_page = paginator.get_page(page_number)
    
    # Get filter options
    programs = MinistryProgram.objects.filter(is_deleted=False).order_by('title')
    actions = MinistryProgramHistory.objects.values_list('action', flat=True).distinct()
    users = MinistryProgramHistory.objects.select_related('changed_by').values(
        'changed_by__id', 'changed_by__first_name', 'changed_by__last_name'
    ).distinct()
    
    context = {
        'history_page': history_page,
        'programs': programs,
        'actions': actions,
        'users': users,
        'current_filters': {
            'program': program_id,
            'action': action_type,
            'user': user_id,
        }
    }
    
    return render(request, 'services/admin/program_history.html', context)
