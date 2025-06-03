from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied
from .services import AnalyticsService
from .models import Report, ScheduledReport, Dashboard, DashboardWidget
from .forms import ReportFilterForm, DashboardConfigForm
import json
import csv
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import logging

logger = logging.getLogger(__name__)


class ExecutiveDashboardView(TemplateView):
    """Executive dashboard view."""
    template_name = 'dashboards/executive.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check permissions
        if not self.request.user.is_staff:
            raise PermissionDenied("You don't have permission to view this dashboard")
        
        # Get date range from request
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        if self.request.GET.get('start_date') and self.request.GET.get('end_date'):
            try:
                start_date = datetime.strptime(self.request.GET['start_date'], '%Y-%m-%d')
                end_date = datetime.strptime(self.request.GET['end_date'], '%Y-%m-%d')
            except ValueError:
                pass
        
        # Get analytics data
        analytics_service = AnalyticsService()
        metrics = analytics_service.get_dashboard_metrics(start_date, end_date)
        
        # Prepare chart data
        context['referral_status_chart'] = json.dumps({
            'labels': list(metrics['referrals']['status_counts'].keys()),
            'data': list(metrics['referrals']['status_counts'].values()),
        })
        
        context['category_chart'] = json.dumps({
            'labels': list(metrics['referrals']['category_counts'].keys()),
            'data': list(metrics['referrals']['category_counts'].values()),
        })
        
        context['geographic_chart'] = json.dumps({
            'labels': list(metrics['geographic'].keys()),
            'data': [v['constituents'] for v in metrics['geographic'].values()],
        })
        
        # Prepare trend chart data
        referral_trend_data = {
            'labels': [item['date'] for item in metrics['trends']['referrals']],
            'datasets': [
                {
                    'label': 'Referrals',
                    'data': [item['count'] for item in metrics['trends']['referrals']],
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.5)',
                },
                {
                    'label': 'New Constituents',
                    'data': [item['count'] for item in metrics['trends']['constituents']],
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.5)',
                }
            ]
        }
        context['trend_chart'] = json.dumps(referral_trend_data)
        
        # Add other metrics to context
        context.update({
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'metrics': metrics,
        })
        
        return context


@login_required
def operational_dashboard_view(request):
    """Operational dashboard for staff."""
    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # Last 7 days for operational view
    
    # Get analytics data
    analytics_service = AnalyticsService()
    
    # Get referral metrics
    referral_metrics = analytics_service.get_referral_metrics(start_date, end_date)
    
    # Get today's activities
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    today_metrics = {
        'new_referrals': analytics_service.get_referral_metrics(today_start, today_end)['total'],
        'completed_referrals': analytics_service.get_referral_metrics(today_start, today_end)['status_counts'].get('completed', 0),
        'new_constituents': analytics_service.get_constituent_metrics(today_start, today_end)['new'],
    }
    
    # Pending tasks
    from apps.referrals.models import Referral
    pending_referrals = Referral.objects.filter(
        status__in=['pending', 'processing']
    ).order_by('priority', 'created_at')[:10]
    
    context = {
        'referral_metrics': referral_metrics,
        'today_metrics': today_metrics,
        'pending_referrals': pending_referrals,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'dashboards/operational.html', context)


@login_required
def chapter_dashboard_view(request):
    """Chapter performance dashboard."""
    analytics_service = AnalyticsService()
    chapter_metrics = analytics_service.get_chapter_metrics()
    
    # Prepare chart data
    chapter_member_chart = {
        'labels': [ch['name'] for ch in chapter_metrics['chapter_details'][:10]],
        'data': [ch['members'] for ch in chapter_metrics['chapter_details'][:10]],
    }
    
    context = {
        'chapter_metrics': chapter_metrics,
        'chapter_member_chart': json.dumps(chapter_member_chart),
    }
    
    return render(request, 'dashboards/chapter.html', context)


@login_required
def custom_report_view(request):
    """Custom report generation view."""
    if request.method == 'POST':
        form = ReportFilterForm(request.POST)
        if form.is_valid():
            # Generate report
            analytics_service = AnalyticsService()
            
            report_type = form.cleaned_data['report_type']
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            filters = {}
            
            # Build filters from form
            for field, value in form.cleaned_data.items():
                if field not in ['report_type', 'start_date', 'end_date', 'format'] and value:
                    filters[field] = value
            
            # Generate report data
            report_data = analytics_service.generate_custom_report(
                report_type, start_date, end_date, filters
            )
            
            # Determine output format
            output_format = form.cleaned_data.get('format', 'pdf')
            
            if output_format == 'csv':
                return export_report_csv(report_data, report_type)
            elif output_format == 'pdf':
                return export_report_pdf(report_data, report_type)
            else:
                # Display report in template
                context = {
                    'form': form,
                    'report_data': report_data,
                    'report_type': report_type,
                }
                return render(request, 'dashboards/custom_report.html', context)
    else:
        form = ReportFilterForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'dashboards/custom_report.html', context)


def export_report_csv(report_data, report_type):
    """Export report data as CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
    
    writer = csv.writer(response)
    
    # Write headers based on report type
    if report_type == 'referrals' and report_data.get('data'):
        headers = list(report_data['data'][0].keys())
        writer.writerow(headers)
        
        # Write data rows
        for row in report_data['data']:
            writer.writerow([row.get(h, '') for h in headers])
    
    return response


def export_report_pdf(report_data, report_type):
    """Export report data as PDF."""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.pdf"'
    
    # Create PDF document
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Add title
    styles = getSampleStyleSheet()
    title = Paragraph(f"{report_type.title()} Report", styles['Title'])
    elements.append(title)
    
    # Add summary if available
    if report_data.get('summary'):
        summary_data = []
        for key, value in report_data['summary'].items():
            summary_data.append([key.replace('_', ' ').title(), str(value)])
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
    
    # Add data table if available
    if report_data.get('data') and len(report_data['data']) > 0:
        # Create table data
        table_data = []
        headers = list(report_data['data'][0].keys())
        table_data.append(headers)
        
        for row in report_data['data'][:50]:  # Limit to 50 rows for PDF
            table_data.append([str(row.get(h, ''))[:50] for h in headers])  # Truncate long text
        
        # Create table
        data_table = Table(table_data)
        data_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(data_table)
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


@login_required
def dashboard_api_view(request, widget_type):
    """API endpoint for dashboard widget data."""
    # Get parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start_date = datetime.now() - timedelta(days=30)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_date = datetime.now()
    
    analytics_service = AnalyticsService()
    
    # Get data based on widget type
    if widget_type == 'referral_status':
        metrics = analytics_service.get_referral_metrics(start_date, end_date)
        data = {
            'labels': list(metrics['status_counts'].keys()),
            'data': list(metrics['status_counts'].values()),
        }
    elif widget_type == 'geographic':
        metrics = analytics_service.get_geographic_distribution()
        data = {
            'labels': list(metrics.keys()),
            'datasets': [
                {
                    'label': 'Constituents',
                    'data': [v['constituents'] for v in metrics.values()],
                },
                {
                    'label': 'Referrals',
                    'data': [v['referrals'] for v in metrics.values()],
                }
            ]
        }
    elif widget_type == 'trends':
        metrics = analytics_service.get_trend_data(start_date, end_date)
        data = {
            'labels': [item['date'] for item in metrics['referrals']],
            'datasets': [
                {
                    'label': 'Referrals',
                    'data': [item['count'] for item in metrics['referrals']],
                },
                {
                    'label': 'Constituents',
                    'data': [item['count'] for item in metrics['constituents']],
                }
            ]
        }
    else:
        return JsonResponse({'error': 'Invalid widget type'}, status=400)
    
    return JsonResponse(data)


@login_required
def save_dashboard_config(request):
    """Save dashboard configuration."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            dashboard_id = data.get('dashboard_id')
            config = data.get('config')
            
            dashboard = get_object_or_404(Dashboard, id=dashboard_id)
            
            # Check permissions
            if dashboard.created_by != request.user and not request.user.is_staff:
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            dashboard.config = config
            dashboard.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f"Error saving dashboard config: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)