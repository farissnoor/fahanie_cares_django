# Generated by Django 4.2.7 on 2025-05-28 10:04

from django.conf import settings
import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('services', '0002_ministryprogram_ministryprogramhistory_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalServiceApplication',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('application_number', models.CharField(db_index=True, max_length=20)),
                ('beneficiary_is_self', models.BooleanField(default=True)),
                ('beneficiary_name', models.CharField(blank=True, max_length=200)),
                ('beneficiary_relationship', models.CharField(blank=True, max_length=100)),
                ('beneficiary_contact', models.CharField(blank=True, max_length=100)),
                ('household_size', models.PositiveSmallIntegerField(default=1)),
                ('household_income', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('reason_for_application', models.TextField()),
                ('supporting_details', models.TextField(blank=True)),
                ('priority_level', models.CharField(choices=[('urgent', 'Urgent'), ('high', 'High'), ('normal', 'Normal'), ('low', 'Low')], default='normal', max_length=10)),
                ('assessment_notes', models.TextField(blank=True)),
                ('home_visit_required', models.BooleanField(default=False)),
                ('home_visit_completed', models.BooleanField(default=False)),
                ('home_visit_report', models.TextField(blank=True)),
                ('supporting_documents', models.TextField(blank=True, max_length=100, null=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('submitted', 'Submitted'), ('under_review', 'Under Review'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('waitlisted', 'Waitlisted'), ('withdrawn', 'Withdrawn')], default='draft', max_length=20)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('assistance_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('assistance_description', models.TextField(blank=True)),
                ('disbursement_date', models.DateField(blank=True, null=True)),
                ('disbursement_method', models.CharField(blank=True, max_length=100)),
                ('follow_up_required', models.BooleanField(default=False)),
                ('follow_up_date', models.DateField(blank=True, null=True)),
                ('follow_up_notes', models.TextField(blank=True)),
                ('notion_id', models.CharField(blank=True, help_text='Notion database ID', max_length=36)),
                ('created_at', models.DateTimeField(blank=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical service application',
                'verbose_name_plural': 'historical service applications',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalServiceProgram',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_at', models.DateTimeField(blank=True, db_index=True, editable=False)),
                ('updated_at', models.DateTimeField(blank=True, editable=False)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('notion_id', models.CharField(blank=True, db_index=True, help_text='Notion database ID for this record', max_length=36)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=200)),
                ('program_type', models.CharField(choices=[('educational', 'Educational Support'), ('health', 'Healthcare Services'), ('livelihood', 'Livelihood Assistance'), ('emergency', 'Emergency Relief'), ('infrastructure', 'Community Infrastructure'), ('social', 'Social Services'), ('youth', 'Youth Development'), ('elderly', 'Senior Citizen Support'), ('pwd', 'PWD Assistance'), ('other', 'Other Services')], max_length=20)),
                ('description', models.TextField()),
                ('objectives', models.TextField()),
                ('eligibility_criteria', models.JSONField(blank=True, default=dict, help_text='Structured eligibility criteria')),
                ('required_documents', models.JSONField(blank=True, default=list, help_text='List of required documents')),
                ('target_beneficiaries', models.CharField(db_index=True, max_length=200)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('application_start', models.DateField(blank=True, null=True)),
                ('application_end', models.DateField(blank=True, null=True)),
                ('total_budget', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('funding_source', models.CharField(blank=True, max_length=200)),
                ('max_beneficiaries', models.PositiveIntegerField(default=0)),
                ('status', models.CharField(choices=[('active', 'Active'), ('planning', 'Planning'), ('completed', 'Completed'), ('suspended', 'Suspended')], default='planning', max_length=20)),
                ('partner_agencies', models.TextField(blank=True)),
                ('partner_organizations', models.TextField(blank=True)),
                ('program_guidelines', models.TextField(blank=True, max_length=100, null=True)),
                ('application_form', models.TextField(blank=True, max_length=100, null=True)),
                ('beneficiary_count', models.PositiveIntegerField(db_index=True, default=0)),
                ('budget_utilized', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('published_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('search_vector', django.contrib.postgres.search.SearchVectorField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical service program',
                'verbose_name_plural': 'historical service programs',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.AddField(
            model_name='serviceapplication',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)ss', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='serviceapplication',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='serviceapplication',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_%(class)ss', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='serviceapplication',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='serviceapplication',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)ss', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='serviceprogram',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_%(class)ss', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='serviceprogram',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='serviceprogram',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deleted_%(class)ss', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='serviceprogram',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='serviceprogram',
            name='search_vector',
            field=django.contrib.postgres.search.SearchVectorField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='serviceprogram',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_%(class)ss', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='serviceprogram',
            name='beneficiary_count',
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
        migrations.AlterField(
            model_name='serviceprogram',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='serviceprogram',
            name='eligibility_criteria',
            field=models.JSONField(blank=True, default=dict, help_text='Structured eligibility criteria'),
        ),
        migrations.AlterField(
            model_name='serviceprogram',
            name='notion_id',
            field=models.CharField(blank=True, db_index=True, help_text='Notion database ID for this record', max_length=36),
        ),
        migrations.AlterField(
            model_name='serviceprogram',
            name='published_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='serviceprogram',
            name='required_documents',
            field=models.JSONField(blank=True, default=list, help_text='List of required documents'),
        ),
        migrations.AlterField(
            model_name='serviceprogram',
            name='target_beneficiaries',
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AddIndex(
            model_name='serviceprogram',
            index=models.Index(fields=['program_type'], name='services_se_program_3b3ed2_idx'),
        ),
        migrations.AddIndex(
            model_name='serviceprogram',
            index=models.Index(fields=['status'], name='services_se_status_ab3676_idx'),
        ),
        migrations.AddIndex(
            model_name='serviceprogram',
            index=models.Index(fields=['start_date'], name='services_se_start_d_9d3d57_idx'),
        ),
        migrations.AddIndex(
            model_name='serviceprogram',
            index=models.Index(fields=['end_date'], name='services_se_end_dat_34bbcd_idx'),
        ),
        migrations.AddIndex(
            model_name='serviceprogram',
            index=models.Index(fields=['coordinator'], name='services_se_coordin_c28aab_idx'),
        ),
        migrations.AddIndex(
            model_name='serviceprogram',
            index=models.Index(fields=['beneficiary_count'], name='services_se_benefic_614c63_idx'),
        ),
        migrations.AddIndex(
            model_name='serviceprogram',
            index=models.Index(fields=['published_at'], name='services_se_publish_d52958_idx'),
        ),
        migrations.AddIndex(
            model_name='serviceprogram',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_vector'], name='services_se_search__75656b_gin'),
        ),
        migrations.AddIndex(
            model_name='serviceprogram',
            index=django.contrib.postgres.indexes.GinIndex(fields=['eligibility_criteria'], name='services_se_eligibi_6d2623_gin'),
        ),
        migrations.AddIndex(
            model_name='serviceprogram',
            index=django.contrib.postgres.indexes.GinIndex(fields=['required_documents'], name='services_se_require_b23f7e_gin'),
        ),
        migrations.AddField(
            model_name='historicalserviceprogram',
            name='coordinator',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalserviceprogram',
            name='created_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalserviceprogram',
            name='deleted_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalserviceprogram',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalserviceprogram',
            name='published_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalserviceprogram',
            name='updated_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalserviceapplication',
            name='applicant',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalserviceapplication',
            name='approved_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalserviceapplication',
            name='created_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalserviceapplication',
            name='deleted_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalserviceapplication',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalserviceapplication',
            name='program',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='services.serviceprogram'),
        ),
        migrations.AddField(
            model_name='historicalserviceapplication',
            name='reviewed_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalserviceapplication',
            name='updated_by',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
    ]
