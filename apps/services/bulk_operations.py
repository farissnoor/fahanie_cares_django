"""
Bulk operations for Ministry Programs.
Handles import/export of PPAs in various formats (CSV, JSON, Excel).
"""

import csv
import json

from datetime import datetime
from decimal import Decimal
from io import StringIO, BytesIO
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import MinistryProgram
from .audit import MinistryProgramAuditService

User = get_user_model()


class MinistryProgramBulkImporter:
    """
    Handles bulk import of Ministry Programs from various file formats.
    """
    
    def __init__(self, user, dry_run=False):
        """
        Initialize the bulk importer.
        
        Args:
            user: User performing the import
            dry_run: If True, validate but don't save records
        """
        self.user = user
        self.dry_run = dry_run
        self.errors = []
        self.warnings = []
        self.created_count = 0
        self.updated_count = 0
        self.skipped_count = 0
    
    def import_from_csv(self, csv_file_content, update_existing=False):
        """
        Import programs from CSV content.
        
        Args:
            csv_file_content: CSV file content as string or file object
            update_existing: Whether to update existing programs
        
        Returns:
            Dict with import results
        """
        try:
            # Parse CSV
            if hasattr(csv_file_content, 'read'):
                csv_content = csv_file_content.read().decode('utf-8')
            else:
                csv_content = csv_file_content
            
            csv_reader = csv.DictReader(StringIO(csv_content))
            
            with transaction.atomic():
                for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        self._process_csv_row(row, row_num, update_existing)
                    except Exception as e:
                        self.errors.append(f"Row {row_num}: {str(e)}")
                
                if self.dry_run or self.errors:
                    transaction.set_rollback(True)
            
            return self._get_import_results()
            
        except Exception as e:
            self.errors.append(f"CSV parsing error: {str(e)}")
            return self._get_import_results()
    
    def import_from_json(self, json_file_content, update_existing=False):
        """
        Import programs from JSON content.
        
        Args:
            json_file_content: JSON file content as string or file object
            update_existing: Whether to update existing programs
        
        Returns:
            Dict with import results
        """
        try:
            # Parse JSON
            if hasattr(json_file_content, 'read'):
                json_content = json_file_content.read().decode('utf-8')
            else:
                json_content = json_file_content
            
            data = json.loads(json_content)
            
            # Handle both single program and array of programs
            if isinstance(data, dict):
                programs_data = [data]
            else:
                programs_data = data
            
            with transaction.atomic():
                for index, program_data in enumerate(programs_data):
                    try:
                        self._process_json_program(program_data, index + 1, update_existing)
                    except Exception as e:
                        self.errors.append(f"Program {index + 1}: {str(e)}")
                
                if self.dry_run or self.errors:
                    transaction.set_rollback(True)
            
            return self._get_import_results()
            
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON parsing error: {str(e)}")
            return self._get_import_results()
        except Exception as e:
            self.errors.append(f"Import error: {str(e)}")
            return self._get_import_results()
    
    def _process_csv_row(self, row, row_num, update_existing):
        """Process a single CSV row."""
        # Clean and validate required fields
        required_fields = ['code', 'title', 'ministry', 'ppa_type', 'start_date', 'end_date']
        for field in required_fields:
            if not row.get(field, '').strip():
                raise ValidationError(f"Missing required field: {field}")
        
        # Parse dates
        try:
            start_date = datetime.strptime(row['start_date'].strip(), '%Y-%m-%d').date()
            end_date = datetime.strptime(row['end_date'].strip(), '%Y-%m-%d').date()
        except ValueError as e:
            raise ValidationError(f"Invalid date format: {str(e)}")
        
        # Validate ministry choice
        ministry_choices = dict(MinistryProgram.MINISTRIES)
        ministry = row['ministry'].strip()
        if ministry not in ministry_choices:
            raise ValidationError(f"Invalid ministry: {ministry}")
        
        # Validate PPA type
        ppa_type_choices = dict(MinistryProgram.PPA_TYPES)
        ppa_type = row['ppa_type'].strip()
        if ppa_type not in ppa_type_choices:
            raise ValidationError(f"Invalid PPA type: {ppa_type}")
        
        # Check if program exists
        code = row['code'].strip()
        existing_program = MinistryProgram.objects.filter(code=code).first()
        
        if existing_program and not update_existing:
            self.skipped_count += 1
            self.warnings.append(f"Row {row_num}: Program {code} already exists (skipped)")
            return
        
        # Prepare program data
        program_data = {
            'code': code,
            'title': row['title'].strip(),
            'ministry': ministry,
            'ppa_type': ppa_type,
            'description': row.get('description', '').strip(),
            'objectives': row.get('objectives', '').strip(),
            'expected_outcomes': row.get('expected_outcomes', '').strip(),
            'key_performance_indicators': row.get('key_performance_indicators', '').strip(),
            'target_beneficiaries': row.get('target_beneficiaries', '').strip(),
            'geographic_coverage': row.get('geographic_coverage', '').strip(),
            'estimated_beneficiaries': int(row.get('estimated_beneficiaries', 0) or 0),
            'implementation_strategy': row.get('implementation_strategy', '').strip(),
            'implementing_units': row.get('implementing_units', '').strip(),
            'partner_agencies': row.get('partner_agencies', '').strip(),
            'total_budget': Decimal(row.get('total_budget', 0) or 0),
            'allocated_budget': Decimal(row.get('allocated_budget', 0) or 0),
            'utilized_budget': Decimal(row.get('utilized_budget', 0) or 0),
            'funding_source': row.get('funding_source', 'national').strip(),
            'funding_details': row.get('funding_details', '').strip(),
            'start_date': start_date,
            'end_date': end_date,
            'duration_months': int(row.get('duration_months', 12) or 12),
            'status': row.get('status', 'draft').strip(),
            'priority_level': row.get('priority_level', 'medium').strip(),
        }
        
        # Create or update program
        if not self.dry_run:
            if existing_program:
                # Update existing
                for field, value in program_data.items():
                    setattr(existing_program, field, value)
                existing_program.last_modified_by = self.user
                existing_program.save()
                
                # Log audit trail
                MinistryProgramAuditService.log_program_action(
                    existing_program, 'update', self.user,
                    reason=f"Bulk update from CSV import (row {row_num})"
                )
                
                self.updated_count += 1
            else:
                # Create new
                program_data['created_by'] = self.user
                program_data['last_modified_by'] = self.user
                program = MinistryProgram.objects.create(**program_data)
                
                # Log audit trail
                MinistryProgramAuditService.log_program_action(
                    program, 'create', self.user,
                    reason=f"Bulk import from CSV (row {row_num})"
                )
                
                self.created_count += 1
    
    def _process_json_program(self, program_data, index, update_existing):
        """Process a single JSON program object."""
        # Similar validation logic as CSV but for JSON structure
        required_fields = ['code', 'title', 'ministry', 'ppa_type', 'start_date', 'end_date']
        for field in required_fields:
            if field not in program_data or not str(program_data[field]).strip():
                raise ValidationError(f"Missing required field: {field}")
        
        # Parse dates if they're strings
        for date_field in ['start_date', 'end_date']:
            if isinstance(program_data[date_field], str):
                try:
                    program_data[date_field] = datetime.strptime(
                        program_data[date_field], '%Y-%m-%d'
                    ).date()
                except ValueError as e:
                    raise ValidationError(f"Invalid {date_field} format: {str(e)}")
        
        # Check if program exists
        code = program_data['code']
        existing_program = MinistryProgram.objects.filter(code=code).first()
        
        if existing_program and not update_existing:
            self.skipped_count += 1
            self.warnings.append(f"Program {index}: Program {code} already exists (skipped)")
            return
        
        # Create or update program
        if not self.dry_run:
            if existing_program:
                # Update existing
                for field, value in program_data.items():
                    if hasattr(existing_program, field):
                        setattr(existing_program, field, value)
                existing_program.last_modified_by = self.user
                existing_program.save()
                
                self.updated_count += 1
            else:
                # Create new
                program_data['created_by'] = self.user
                program_data['last_modified_by'] = self.user
                program = MinistryProgram.objects.create(**program_data)
                
                self.created_count += 1
    
    def _get_import_results(self):
        """Get import results summary."""
        return {
            'success': len(self.errors) == 0,
            'created': self.created_count,
            'updated': self.updated_count,
            'skipped': self.skipped_count,
            'errors': self.errors,
            'warnings': self.warnings,
            'dry_run': self.dry_run,
        }


class MinistryProgramBulkExporter:
    """
    Handles bulk export of Ministry Programs to various file formats.
    """
    
    def __init__(self, user):
        """
        Initialize the bulk exporter.
        
        Args:
            user: User performing the export
        """
        self.user = user
    
    def export_to_csv(self, queryset=None, fields=None):
        """
        Export programs to CSV format.
        
        Args:
            queryset: QuerySet of programs to export (default: all active)
            fields: List of fields to include (default: all exportable fields)
        
        Returns:
            CSV content as string
        """
        if queryset is None:
            queryset = MinistryProgram.objects.filter(is_deleted=False)
        
        if fields is None:
            fields = self._get_exportable_fields()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        headers = [field.replace('_', ' ').title() for field in fields]
        writer.writerow(headers)
        
        # Write data
        for program in queryset:
            row = []
            for field in fields:
                value = getattr(program, field, '')
                
                # Handle special field types
                if hasattr(value, 'strftime'):  # Date/datetime
                    value = value.strftime('%Y-%m-%d')
                elif hasattr(value, '__call__'):  # Method
                    value = value()
                elif value is None:
                    value = ''
                
                row.append(str(value))
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def export_to_json(self, queryset=None, fields=None):
        """
        Export programs to JSON format.
        
        Args:
            queryset: QuerySet of programs to export (default: all active)
            fields: List of fields to include (default: all exportable fields)
        
        Returns:
            JSON content as string
        """
        if queryset is None:
            queryset = MinistryProgram.objects.filter(is_deleted=False)
        
        if fields is None:
            fields = self._get_exportable_fields()
        
        programs_data = []
        
        for program in queryset:
            program_data = {}
            for field in fields:
                value = getattr(program, field, None)
                
                # Handle special field types
                if hasattr(value, 'strftime'):  # Date/datetime
                    value = value.strftime('%Y-%m-%d')
                elif hasattr(value, '__call__'):  # Method
                    value = value()
                elif isinstance(value, Decimal):
                    value = float(value)
                
                program_data[field] = value
            
            programs_data.append(program_data)
        
        return json.dumps(programs_data, indent=2, default=str)
    
    def export_to_excel(self, queryset=None, fields=None):
        """
        Export programs to Excel format.
        
        Args:
            queryset: QuerySet of programs to export (default: all active)
            fields: List of fields to include (default: all exportable fields)
        
        Returns:
            Excel file content as bytes
        """
        if queryset is None:
            queryset = MinistryProgram.objects.filter(is_deleted=False)
        
        if fields is None:
            fields = self._get_exportable_fields()
        
        # Prepare data for DataFrame
        data = []
        for program in queryset:
            row = {}
            for field in fields:
                value = getattr(program, field, None)
                
                # Handle special field types
                if hasattr(value, '__call__'):  # Method
                    value = value()
                elif isinstance(value, Decimal):
                    value = float(value)
                
                row[field.replace('_', ' ').title()] = value
            
            data.append(row)
        
        # Create DataFrame and Excel file
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Ministry Programs', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    def _get_exportable_fields(self):
        """Get list of fields suitable for export."""
        return [
            'code', 'title', 'ministry', 'ppa_type', 'description', 'objectives',
            'expected_outcomes', 'key_performance_indicators', 'target_beneficiaries',
            'geographic_coverage', 'estimated_beneficiaries', 'implementation_strategy',
            'implementing_units', 'partner_agencies', 'total_budget', 'allocated_budget',
            'utilized_budget', 'funding_source', 'funding_details', 'start_date',
            'end_date', 'duration_months', 'status', 'priority_level', 'is_public',
            'is_featured', 'created_at', 'updated_at'
        ]


class MinistryProgramBulkOperations:
    """
    High-level interface for bulk operations on Ministry Programs.
    """
    
    @staticmethod
    def import_programs(file_content, file_format, user, update_existing=False, dry_run=False):
        """
        Import programs from file content.
        
        Args:
            file_content: File content (string or file object)
            file_format: File format ('csv', 'json')
            user: User performing the import
            update_existing: Whether to update existing programs
            dry_run: Whether to validate without saving
        
        Returns:
            Import results dictionary
        """
        importer = MinistryProgramBulkImporter(user, dry_run=dry_run)
        
        if file_format.lower() == 'csv':
            return importer.import_from_csv(file_content, update_existing)
        elif file_format.lower() == 'json':
            return importer.import_from_json(file_content, update_existing)
        else:
            return {
                'success': False,
                'errors': [f'Unsupported file format: {file_format}'],
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'warnings': [],
                'dry_run': dry_run
            }
    
    @staticmethod
    def export_programs(file_format, user, ministry=None, status=None, fields=None):
        """
        Export programs to specified format.
        
        Args:
            file_format: Export format ('csv', 'json', 'excel')
            user: User performing the export
            ministry: Filter by ministry (optional)
            status: Filter by status (optional)
            fields: Fields to include (optional)
        
        Returns:
            Tuple of (content, content_type, filename)
        """
        exporter = MinistryProgramBulkExporter(user)
        
        # Build queryset with filters
        queryset = MinistryProgram.objects.filter(is_deleted=False)
        
        if ministry:
            queryset = queryset.filter(ministry=ministry)
        
        if status:
            queryset = queryset.filter(status=status)
        
        # Generate filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"ministry_programs_{timestamp}"
        
        # Export based on format
        if file_format.lower() == 'csv':
            content = exporter.export_to_csv(queryset, fields)
            content_type = 'text/csv'
            filename = f"{base_filename}.csv"
        elif file_format.lower() == 'json':
            content = exporter.export_to_json(queryset, fields)
            content_type = 'application/json'
            filename = f"{base_filename}.json"
        elif file_format.lower() == 'excel':
            content = exporter.export_to_excel(queryset, fields)
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f"{base_filename}.xlsx"
        else:
            raise ValueError(f'Unsupported export format: {file_format}')
        
        return content, content_type, filename
    
    @staticmethod
    def get_import_template(file_format='csv'):
        """
        Generate an import template file.
        
        Args:
            file_format: Template format ('csv', 'json')
        
        Returns:
            Template content as string
        """
        sample_data = {
            'code': 'MSSD-2024-001',
            'title': 'Sample Social Protection Program',
            'ministry': 'mssd',
            'ppa_type': 'program',
            'description': 'A comprehensive social protection program for vulnerable families',
            'objectives': 'Provide social safety net for low-income households',
            'expected_outcomes': 'Reduced poverty and improved social welfare',
            'key_performance_indicators': 'Number of beneficiaries, poverty reduction rate',
            'target_beneficiaries': 'Low-income families, elderly, PWDs',
            'geographic_coverage': 'All provinces in BARMM',
            'estimated_beneficiaries': '10000',
            'implementation_strategy': 'Partnership with LGUs and NGOs',
            'implementing_units': 'MSSD Field Offices',
            'partner_agencies': 'DSWD, LGUs, NGO Partners',
            'total_budget': '50000000.00',
            'allocated_budget': '50000000.00',
            'utilized_budget': '0.00',
            'funding_source': 'national',
            'funding_details': 'National government allocation',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'duration_months': '12',
            'status': 'draft',
            'priority_level': 'high'
        }
        
        if file_format.lower() == 'csv':
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=sample_data.keys())
            writer.writeheader()
            writer.writerow(sample_data)
            return output.getvalue()
        
        elif file_format.lower() == 'json':
            return json.dumps([sample_data], indent=2)
        
        else:
            raise ValueError(f'Unsupported template format: {file_format}')