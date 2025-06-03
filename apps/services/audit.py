"""
Enhanced audit trail system for Ministry Programs.
Provides comprehensive tracking of all changes and administrative actions.
"""

import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.core.serializers.json import DjangoJSONEncoder
from .models import MinistryProgram, MinistryProgramHistory

User = get_user_model()


class MinistryProgramAuditService:
    """
    Service class for enhanced audit trail functionality.
    Provides methods for tracking, querying, and reporting on program changes.
    """
    
    @staticmethod
    def log_program_action(program, action_type, user, request=None, reason=None, 
                          comments=None, changed_fields=None, old_values=None, new_values=None):
        """
        Log a program action to the audit trail.
        
        Args:
            program: MinistryProgram instance
            action_type: Type of action (create, update, delete, etc.)
            user: User who performed the action
            request: HTTP request object (optional)
            reason: Reason for the action (optional)
            comments: Additional comments (optional)
            changed_fields: List of changed field names (optional)
            old_values: Dict of old field values (optional) 
            new_values: Dict of new field values (optional)
        """
        
        audit_data = {
            'program': program,
            'action_type': action_type,
            'changed_by': user,
            'changed_at': timezone.now(),
            'reason': reason or '',
            'comments': comments or '',
            'changed_fields': changed_fields or [],
            'old_values': old_values or {},
            'new_values': new_values or {},
        }
        
        # Extract request information if available
        if request:
            audit_data['ip_address'] = MinistryProgramAuditService.get_client_ip(request)
            audit_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        return MinistryProgramHistory.objects.create(**audit_data)
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def get_program_history(program, action_types=None, start_date=None, end_date=None, user=None):
        """
        Get filtered history for a specific program.
        
        Args:
            program: MinistryProgram instance
            action_types: List of action types to filter by
            start_date: Start date for filtering
            end_date: End date for filtering
            user: User who made changes
        
        Returns:
            QuerySet of MinistryProgramHistory instances
        """
        queryset = MinistryProgramHistory.objects.filter(program=program)
        
        if action_types:
            queryset = queryset.filter(action_type__in=action_types)
        
        if start_date:
            queryset = queryset.filter(changed_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(changed_at__lte=end_date)
        
        if user:
            queryset = queryset.filter(changed_by=user)
        
        return queryset.order_by('-changed_at')
    
    @staticmethod
    def get_user_activity(user, start_date=None, end_date=None, ministry=None):
        """
        Get audit trail for a specific user's activities.
        
        Args:
            user: User instance
            start_date: Start date for filtering
            end_date: End date for filtering
            ministry: Ministry to filter by
        
        Returns:
            QuerySet of MinistryProgramHistory instances
        """
        queryset = MinistryProgramHistory.objects.filter(changed_by=user)
        
        if start_date:
            queryset = queryset.filter(changed_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(changed_at__lte=end_date)
        
        if ministry:
            queryset = queryset.filter(program__ministry=ministry)
        
        return queryset.order_by('-changed_at')
    
    @staticmethod
    def get_ministry_activity(ministry, days=30):
        """
        Get recent activity for a specific ministry.
        
        Args:
            ministry: Ministry code (e.g., 'mssd', 'mafar')
            days: Number of days to look back
        
        Returns:
            QuerySet of MinistryProgramHistory instances
        """
        start_date = timezone.now() - timedelta(days=days)
        
        return MinistryProgramHistory.objects.filter(
            program__ministry=ministry,
            changed_at__gte=start_date
        ).order_by('-changed_at')
    
    @staticmethod
    def get_activity_summary(start_date=None, end_date=None):
        """
        Get summary of audit trail activity.
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
        
        Returns:
            Dict with activity statistics
        """
        queryset = MinistryProgramHistory.objects.all()
        
        if start_date:
            queryset = queryset.filter(changed_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(changed_at__lte=end_date)
        
        # Activity by action type
        action_counts = queryset.values('action_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Activity by ministry
        ministry_counts = queryset.values('program__ministry').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Most active users
        user_counts = queryset.values('changed_by__first_name', 'changed_by__last_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return {
            'total_actions': queryset.count(),
            'action_counts': list(action_counts),
            'ministry_counts': list(ministry_counts),
            'top_users': list(user_counts),
            'date_range': {
                'start': start_date,
                'end': end_date
            }
        }
    
    @staticmethod
    def detect_bulk_changes(user, time_window_minutes=5):
        """
        Detect bulk changes made by a user within a time window.
        
        Args:
            user: User instance
            time_window_minutes: Time window to consider for bulk changes
        
        Returns:
            List of bulk change sessions
        """
        start_time = timezone.now() - timedelta(minutes=time_window_minutes)
        
        recent_changes = MinistryProgramHistory.objects.filter(
            changed_by=user,
            changed_at__gte=start_time
        ).order_by('changed_at')
        
        bulk_sessions = []
        current_session = []
        last_change_time = None
        
        for change in recent_changes:
            if (last_change_time is None or 
                change.changed_at - last_change_time <= timedelta(seconds=30)):
                current_session.append(change)
            else:
                if len(current_session) >= 3:  # Consider 3+ changes as bulk
                    bulk_sessions.append(current_session)
                current_session = [change]
            
            last_change_time = change.changed_at
        
        # Don't forget the last session
        if len(current_session) >= 3:
            bulk_sessions.append(current_session)
        
        return bulk_sessions
    
    @staticmethod
    def generate_audit_report(program, format='json'):
        """
        Generate comprehensive audit report for a program.
        
        Args:
            program: MinistryProgram instance
            format: Output format ('json', 'csv', 'html')
        
        Returns:
            Formatted audit report
        """
        history = MinistryProgramHistory.objects.filter(program=program).order_by('changed_at')
        
        report_data = {
            'program': {
                'code': program.code,
                'title': program.title,
                'ministry': program.get_ministry_display(),
                'status': program.get_status_display(),
                'created_at': program.created_at,
                'created_by': program.created_by.get_full_name() if program.created_by else None,
            },
            'history': [],
            'summary': {
                'total_changes': history.count(),
                'unique_users': history.values('changed_by').distinct().count(),
                'action_counts': {},
                'first_change': None,
                'last_change': None,
            }
        }
        
        # Process history records
        action_counts = {}
        
        for record in history:
            history_item = {
                'timestamp': record.changed_at,
                'action': record.get_action_type_display(),
                'user': record.changed_by.get_full_name(),
                'user_type': record.changed_by.user_type,
                'changed_fields': record.changed_fields,
                'reason': record.reason,
                'comments': record.comments,
                'ip_address': record.ip_address,
            }
            
            # Add field changes if available
            if record.changed_fields and record.old_values and record.new_values:
                history_item['changes'] = {}
                for field in record.changed_fields:
                    history_item['changes'][field] = {
                        'old': record.old_values.get(field),
                        'new': record.new_values.get(field)
                    }
            
            report_data['history'].append(history_item)
            
            # Count actions
            action_counts[record.action_type] = action_counts.get(record.action_type, 0) + 1
        
        # Update summary
        report_data['summary']['action_counts'] = action_counts
        if history.exists():
            report_data['summary']['first_change'] = history.first().changed_at
            report_data['summary']['last_change'] = history.last().changed_at
        
        # Format output
        if format == 'json':
            return json.dumps(report_data, cls=DjangoJSONEncoder, indent=2)
        elif format == 'csv':
            return MinistryProgramAuditService._format_csv_report(report_data)
        elif format == 'html':
            return MinistryProgramAuditService._format_html_report(report_data)
        else:
            return report_data
    
    @staticmethod
    def _format_csv_report(report_data):
        """Format audit report as CSV."""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Timestamp', 'Action', 'User', 'User Type', 'Changed Fields',
            'Reason', 'Comments', 'IP Address'
        ])
        
        # Data rows
        for item in report_data['history']:
            writer.writerow([
                item['timestamp'],
                item['action'],
                item['user'],
                item['user_type'],
                ', '.join(item['changed_fields']),
                item['reason'],
                item['comments'],
                item['ip_address'] or ''
            ])
        
        return output.getvalue()
    
    @staticmethod
    def _format_html_report(report_data):
        """Format audit report as HTML."""
        html = f"""
        <html>
        <head>
            <title>Audit Report - {report_data['program']['title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .summary {{ background-color: #f9f9f9; padding: 15px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>Audit Report</h1>
            
            <div class="summary">
                <h2>Program Information</h2>
                <p><strong>Code:</strong> {report_data['program']['code']}</p>
                <p><strong>Title:</strong> {report_data['program']['title']}</p>
                <p><strong>Ministry:</strong> {report_data['program']['ministry']}</p>
                <p><strong>Status:</strong> {report_data['program']['status']}</p>
                
                <h3>Summary</h3>
                <p><strong>Total Changes:</strong> {report_data['summary']['total_changes']}</p>
                <p><strong>Unique Users:</strong> {report_data['summary']['unique_users']}</p>
            </div>
            
            <h2>Change History</h2>
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Action</th>
                        <th>User</th>
                        <th>Changed Fields</th>
                        <th>Reason</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in report_data['history']:
            html += f"""
                    <tr>
                        <td>{item['timestamp']}</td>
                        <td>{item['action']}</td>
                        <td>{item['user']} ({item['user_type']})</td>
                        <td>{', '.join(item['changed_fields'])}</td>
                        <td>{item['reason']}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def check_compliance(program):
        """
        Check compliance requirements for program audit trail.
        
        Args:
            program: MinistryProgram instance
        
        Returns:
            Dict with compliance status and recommendations
        """
        history = MinistryProgramHistory.objects.filter(program=program)
        
        compliance_report = {
            'compliant': True,
            'issues': [],
            'recommendations': [],
            'checks': {
                'has_creation_record': False,
                'has_approval_record': False,
                'changes_documented': True,
                'recent_activity_tracked': True,
            }
        }
        
        # Check for creation record
        creation_record = history.filter(action_type='create').exists()
        compliance_report['checks']['has_creation_record'] = creation_record
        if not creation_record:
            compliance_report['issues'].append('No creation record found in audit trail')
            compliance_report['compliant'] = False
        
        # Check for approval record if program is approved
        if program.status == 'active' and program.approved_at:
            approval_record = history.filter(action_type='approve').exists()
            compliance_report['checks']['has_approval_record'] = approval_record
            if not approval_record:
                compliance_report['issues'].append('Program is approved but no approval record in audit trail')
                compliance_report['recommendations'].append('Add approval record to audit trail')
        
        # Check that all changes have proper documentation
        undocumented_changes = history.filter(
            action_type='update',
            reason__isnull=True
        ).count()
        
        if undocumented_changes > 0:
            compliance_report['checks']['changes_documented'] = False
            compliance_report['issues'].append(f'{undocumented_changes} changes lack proper documentation')
            compliance_report['recommendations'].append('Require reason for all program changes')
            compliance_report['compliant'] = False
        
        # Check for recent activity if program is active
        if program.status == 'active':
            recent_activity = history.filter(
                changed_at__gte=timezone.now() - timedelta(days=90)
            ).exists()
            
            compliance_report['checks']['recent_activity_tracked'] = recent_activity
            if not recent_activity:
                compliance_report['recommendations'].append('Consider periodic review and update of active programs')
        
        return compliance_report