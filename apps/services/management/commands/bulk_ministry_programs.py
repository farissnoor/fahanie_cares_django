"""
Management command for bulk operations on Ministry Programs.
Supports import from CSV/JSON and export to various formats.
"""

import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.services.bulk_operations import MinistryProgramBulkOperations
from apps.services.models import MinistryProgram

User = get_user_model()


class Command(BaseCommand):
    help = 'Perform bulk operations on Ministry Programs (import/export)'
    
    def add_arguments(self, parser):
        # Subcommands
        subparsers = parser.add_subparsers(dest='operation', help='Bulk operation to perform')
        
        # Import command
        import_parser = subparsers.add_parser('import', help='Import programs from file')
        import_parser.add_argument('file_path', type=str, help='Path to import file')
        import_parser.add_argument(
            '--format',
            choices=['csv', 'json'],
            default='csv',
            help='File format (default: csv)'
        )
        import_parser.add_argument(
            '--user',
            type=str,
            required=True,
            help='Username of user performing import'
        )
        import_parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing programs'
        )
        import_parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate without saving'
        )
        
        # Export command
        export_parser = subparsers.add_parser('export', help='Export programs to file')
        export_parser.add_argument('output_path', type=str, help='Output file path')
        export_parser.add_argument(
            '--format',
            choices=['csv', 'json', 'excel'],
            default='csv',
            help='Export format (default: csv)'
        )
        export_parser.add_argument(
            '--user',
            type=str,
            required=True,
            help='Username of user performing export'
        )
        export_parser.add_argument(
            '--ministry',
            choices=[choice[0] for choice in MinistryProgram.MINISTRIES],
            help='Filter by ministry'
        )
        export_parser.add_argument(
            '--status',
            choices=[choice[0] for choice in MinistryProgram.STATUS_CHOICES],
            help='Filter by status'
        )
        
        # Template command
        template_parser = subparsers.add_parser('template', help='Generate import template')
        template_parser.add_argument('output_path', type=str, help='Output template file path')
        template_parser.add_argument(
            '--format',
            choices=['csv', 'json'],
            default='csv',
            help='Template format (default: csv)'
        )
        
        # Stats command
        stats_parser = subparsers.add_parser('stats', help='Show database statistics')
        stats_parser.add_argument(
            '--ministry',
            choices=[choice[0] for choice in MinistryProgram.MINISTRIES],
            help='Filter by ministry'
        )
    
    def handle(self, *args, **options):
        operation = options['operation']
        
        if not operation:
            self.print_help('manage.py', 'bulk_ministry_programs')
            return
        
        try:
            if operation == 'import':
                self.handle_import(options)
            elif operation == 'export':
                self.handle_export(options)
            elif operation == 'template':
                self.handle_template(options)
            elif operation == 'stats':
                self.handle_stats(options)
            else:
                raise CommandError(f'Unknown operation: {operation}')
                
        except Exception as e:
            raise CommandError(f'Operation failed: {str(e)}')
    
    def handle_import(self, options):
        """Handle import operation."""
        file_path = options['file_path']
        file_format = options['format']
        username = options['user']
        update_existing = options['update']
        dry_run = options['dry_run']
        
        # Validate file exists
        if not os.path.exists(file_path):
            raise CommandError(f'File not found: {file_path}')
        
        # Get user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User not found: {username}')
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        self.stdout.write(f'Importing programs from {file_path}...')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))
        
        # Perform import
        results = MinistryProgramBulkOperations.import_programs(
            file_content=file_content,
            file_format=file_format,
            user=user,
            update_existing=update_existing,
            dry_run=dry_run
        )
        
        # Display results
        self.display_import_results(results)
    
    def handle_export(self, options):
        """Handle export operation."""
        output_path = options['output_path']
        file_format = options['format']
        username = options['user']
        ministry = options.get('ministry')
        status = options.get('status')
        
        # Get user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User not found: {username}')
        
        self.stdout.write(f'Exporting programs to {output_path}...')
        
        # Perform export
        content, content_type, filename = MinistryProgramBulkOperations.export_programs(
            file_format=file_format,
            user=user,
            ministry=ministry,
            status=status
        )
        
        # Write to file
        if file_format == 'excel':
            with open(output_path, 'wb') as f:
                f.write(content)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully exported programs to {output_path}')
        )
        
        # Show export stats
        from apps.services.models import MinistryProgram
        
        queryset = MinistryProgram.objects.filter(is_deleted=False)
        if ministry:
            queryset = queryset.filter(ministry=ministry)
        if status:
            queryset = queryset.filter(status=status)
        
        self.stdout.write(f'Exported {queryset.count()} programs')
    
    def handle_template(self, options):
        """Handle template generation."""
        output_path = options['output_path']
        file_format = options['format']
        
        self.stdout.write(f'Generating {file_format.upper()} template...')
        
        # Generate template
        template_content = MinistryProgramBulkOperations.get_import_template(file_format)
        
        # Write template to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        self.stdout.write(
            self.style.SUCCESS(f'Template generated: {output_path}')
        )
        
        self.stdout.write(
            'You can now fill in this template with your program data and import it.'
        )
    
    def handle_stats(self, options):
        """Handle statistics display."""
        ministry = options.get('ministry')
        
        from django.db.models import Count, Sum
        from apps.services.models import MinistryProgram
        
        self.stdout.write(self.style.HTTP_INFO('Ministry Programs Statistics'))
        self.stdout.write('=' * 50)
        
        # Base queryset
        queryset = MinistryProgram.objects.filter(is_deleted=False)
        if ministry:
            queryset = queryset.filter(ministry=ministry)
            ministry_name = dict(MinistryProgram.MINISTRIES)[ministry]
            self.stdout.write(f'Ministry: {ministry_name}')
            self.stdout.write('-' * 30)
        
        # Total counts
        total_programs = queryset.count()
        self.stdout.write(f'Total Programs: {total_programs}')
        
        if total_programs == 0:
            self.stdout.write('No programs found.')
            return
        
        # By status
        self.stdout.write('\nBy Status:')
        status_counts = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for item in status_counts:
            status_display = dict(MinistryProgram.STATUS_CHOICES)[item['status']]
            self.stdout.write(f'  {status_display}: {item["count"]}')
        
        # By ministry (if not filtered)
        if not ministry:
            self.stdout.write('\nBy Ministry:')
            ministry_counts = queryset.values('ministry').annotate(
                count=Count('id')
            ).order_by('-count')
            
            for item in ministry_counts:
                ministry_display = dict(MinistryProgram.MINISTRIES)[item['ministry']]
                self.stdout.write(f'  {ministry_display}: {item["count"]}')
        
        # By PPA type
        self.stdout.write('\nBy Type:')
        type_counts = queryset.values('ppa_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for item in type_counts:
            type_display = dict(MinistryProgram.PPA_TYPES)[item['ppa_type']]
            self.stdout.write(f'  {type_display}: {item["count"]}')
        
        # Budget information
        budget_stats = queryset.aggregate(
            total_budget=Sum('total_budget'),
            allocated_budget=Sum('allocated_budget'),
            utilized_budget=Sum('utilized_budget')
        )
        
        self.stdout.write('\nBudget Summary:')
        for key, value in budget_stats.items():
            if value:
                self.stdout.write(f'  {key.replace("_", " ").title()}: ₱{value:,.2f}')
        
        # Recent activity
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        recent_date = timezone.now() - timedelta(days=30)
        recent_programs = queryset.filter(created_at__gte=recent_date).count()
        
        self.stdout.write(f'\nRecent Activity (last 30 days):')
        self.stdout.write(f'  New Programs: {recent_programs}')
    
    def display_import_results(self, results):
        """Display import results in a formatted way."""
        if results['success']:
            self.stdout.write(self.style.SUCCESS('Import completed successfully!'))
        else:
            self.stdout.write(self.style.ERROR('Import completed with errors.'))
        
        # Summary
        self.stdout.write('\nSummary:')
        self.stdout.write(f'  Created: {results["created"]}')
        self.stdout.write(f'  Updated: {results["updated"]}')
        self.stdout.write(f'  Skipped: {results["skipped"]}')
        
        if results['dry_run']:
            self.stdout.write(self.style.WARNING('  (Dry run - no changes saved)'))
        
        # Warnings
        if results['warnings']:
            self.stdout.write(self.style.WARNING(f'\nWarnings ({len(results["warnings"])}):'))
            for warning in results['warnings']:
                self.stdout.write(f'  - {warning}')
        
        # Errors
        if results['errors']:
            self.stdout.write(self.style.ERROR(f'\nErrors ({len(results["errors"])}):'))
            for error in results['errors']:
                self.stdout.write(f'  - {error}')
        
        # Recommendations
        if not results['success']:
            self.stdout.write('\nRecommendations:')
            self.stdout.write('  - Fix the errors above and try again')
            self.stdout.write('  - Use --dry-run to validate before importing')
            self.stdout.write('  - Check the import template for correct format')
        elif results['warnings']:
            self.stdout.write('\nRecommendations:')
            self.stdout.write('  - Review the warnings above')
            self.stdout.write('  - Consider using --update to update existing programs')