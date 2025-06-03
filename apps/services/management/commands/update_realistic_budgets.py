"""
Update ministry program budgets with realistic amounts based on research.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.services.models import MinistryProgram
from apps.services.audit import MinistryProgramAuditService

User = get_user_model()


class Command(BaseCommand):
    help = 'Update ministry program budgets with realistic amounts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Username for audit trail (default: admin)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show changes without applying them'
        )
    
    def handle(self, *args, **options):
        username = options['user']
        dry_run = options['dry_run']
        
        # Get user for audit trail
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" not found.')
            )
            return
        
        # Realistic budget updates based on research
        budget_updates = {
            # MSSD Programs (realistic regional budgets)
            'MSSD-2024-001': Decimal('1200000000.00'),  # 4Ps - ₱1.2B
            'MSSD-2024-002': Decimal('350000000.00'),   # SLP - ₱350M
            'MSSD-2024-003': Decimal('500000000.00'),   # Social Pension - ₱500M
            'MSSD-2024-004': Decimal('1000000000.00'),  # KALAHI-CIDSS - ₱1B
            'MSSD-2024-005': Decimal('250000000.00'),   # AICS - ₱250M
            'MSSD-2024-006': Decimal('600000000.00'),   # Feeding Program - ₱600M
            'MSSD-2024-007': Decimal('400000000.00'),   # MCCT - ₱400M
            'MSSD-2024-008': Decimal('120000000.00'),   # Mental Health - ₱120M
            
            # MAFAR Programs (agriculture/fisheries realistic budgets)
            'MAFAR-2024-001': Decimal('1800000000.00'), # EU BAEP - ₱1.8B
            'MAFAR-2024-002': Decimal('2500000000.00'), # World Bank MRDP - ₱2.5B
            'MAFAR-2024-003': Decimal('1200000000.00'), # Rice Industry - ₱1.2B
            'MAFAR-2024-004': Decimal('650000000.00'),  # Fisheries - ₱650M
            'MAFAR-2024-005': Decimal('450000000.00'),  # Coconut - ₱450M
            'MAFAR-2024-006': Decimal('300000000.00'),  # Halal Livestock - ₱300M
            'MAFAR-2024-007': Decimal('1500000000.00'), # Agrarian Reform - ₱1.5B
            
            # MTIT Programs (trade/industry realistic budgets)
            'MTIT-2024-001': Decimal('800000000.00'),   # Halal Industry - ₱800M
            'MTIT-2024-002': Decimal('150000000.00'),   # Negosyo Centers - ₱150M
            'MTIT-2024-003': Decimal('900000000.00'),   # Tourism - ₱900M
            'MTIT-2024-004': Decimal('300000000.00'),   # Export Development - ₱300M
            'MTIT-2024-005': Decimal('1200000000.00'),  # Industrial Development - ₱1.2B
            'MTIT-2024-006': Decimal('100000000.00'),   # Women Entrepreneurs - ₱100M
            'MTIT-2024-007': Decimal('200000000.00'),   # Digital Economy - ₱200M
        }
        
        self.stdout.write('Updating ministry program budgets with realistic amounts...')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))
        
        updated_count = 0
        total_old_budget = Decimal('0')
        total_new_budget = Decimal('0')
        
        for program_code, new_budget in budget_updates.items():
            try:
                program = MinistryProgram.objects.get(code=program_code)
                old_budget = program.total_budget
                old_allocated = program.allocated_budget
                
                total_old_budget += old_budget
                total_new_budget += new_budget
                
                if dry_run:
                    self.stdout.write(
                        f'  {program_code}: ₱{old_budget/1000000:.0f}M → ₱{new_budget/1000000:.0f}M'
                    )
                else:
                    # Update budget amounts
                    program.total_budget = new_budget
                    program.allocated_budget = new_budget
                    program.last_modified_by = user
                    program.save()
                    
                    # Create audit trail
                    MinistryProgramAuditService.log_program_action(
                        program=program,
                        action_type='update',
                        user=user,
                        reason='Budget update to realistic amounts based on research',
                        changed_fields=['total_budget', 'allocated_budget'],
                        old_values={
                            'total_budget': str(old_budget),
                            'allocated_budget': str(old_allocated)
                        },
                        new_values={
                            'total_budget': str(new_budget),
                            'allocated_budget': str(new_budget)
                        }
                    )
                    
                    self.stdout.write(
                        f'  ✓ Updated {program_code}: ₱{old_budget/1000000:.0f}M → ₱{new_budget/1000000:.0f}M'
                    )
                
                updated_count += 1
                
            except MinistryProgram.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'  ! Program {program_code} not found')
                )
        
        # Summary
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  Programs updated: {updated_count}')
        self.stdout.write(f'  Total budget before: ₱{total_old_budget/1000000000:.1f}B')
        self.stdout.write(f'  Total budget after: ₱{total_new_budget/1000000000:.1f}B')
        self.stdout.write(f'  Reduction: ₱{(total_old_budget-total_new_budget)/1000000000:.1f}B')
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully updated {updated_count} program budgets!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\nRun without --dry-run to apply changes')
            )