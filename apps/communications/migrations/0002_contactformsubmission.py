# Generated manually
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('communications', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactFormSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('middle_name', models.CharField(blank=True, max_length=100, null=True)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, validators=[django.core.validators.EmailValidator()])),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('subject', models.CharField(choices=[('assistance', 'Request Assistance'), ('feedback', 'Provide Feedback'), ('volunteer', 'Volunteer Opportunities'), ('chapter', 'Chapter Inquiries'), ('other', 'Other')], max_length=20)),
                ('message', models.TextField()),
                ('form_source', models.CharField(help_text='Which page/form this submission came from', max_length=50)),
                ('status', models.CharField(choices=[('new', 'New'), ('in_progress', 'In Progress'), ('resolved', 'Resolved'), ('closed', 'Closed')], default='new', max_length=20)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('internal_notes', models.TextField(blank=True, help_text='Internal notes for staff use', null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_contact_submissions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Contact Form Submission',
                'verbose_name_plural': 'Contact Form Submissions',
                'ordering': ['-submitted_at'],
            },
        ),
    ]