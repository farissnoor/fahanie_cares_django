from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from .models import (
    LegislativeSession, LegislativeMeasure, LegislativeAction,
    Committee, CommitteeMembership, CommitteeHearing,
    PlenarySession, SpeechPrivilege, OversightActivity, VotingRecord
)

User = get_user_model()


class LegislativeSessionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_create_session(self):
        session = LegislativeSession.objects.create(
            session_number='First Regular',
            congress_number='19th',
            start_date=date.today(),
            is_current=True
        )
        self.assertEqual(str(session), '19th Congress - First Regular Session')
        
    def test_only_one_current_session(self):
        session1 = LegislativeSession.objects.create(
            session_number='First Regular',
            congress_number='19th',
            start_date=date.today(),
            is_current=True
        )
        
        session2 = LegislativeSession.objects.create(
            session_number='Second Regular',
            congress_number='19th',
            start_date=date.today() + timedelta(days=365),
            is_current=True
        )
        
        session1.refresh_from_db()
        self.assertFalse(session1.is_current)
        self.assertTrue(session2.is_current)


class LegislativeMeasureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.session = LegislativeSession.objects.create(
            session_number='First Regular',
            congress_number='19th',
            start_date=date.today(),
            is_current=True
        )
        
    def test_create_measure(self):
        measure = LegislativeMeasure.objects.create(
            session=self.session,
            measure_type='bill',
            number='HB 1234',
            title='An Act to Improve Public Services',
            abstract='This act aims to improve public services.',
            principal_author=self.user,
            status='draft'
        )
        self.assertEqual(str(measure), 'House Bill HB 1234: An Act to Improve Public Services')
        
    def test_days_since_filing(self):
        measure = LegislativeMeasure.objects.create(
            session=self.session,
            measure_type='bill',
            number='HB 1234',
            title='Test Bill',
            abstract='Test abstract',
            principal_author=self.user,
            filed_date=date.today() - timedelta(days=10)
        )
        self.assertEqual(measure.days_since_filing, 10)


class CommitteeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_create_committee(self):
        committee = Committee.objects.create(
            name='Committee on Health',
            acronym='COH',
            committee_type='standing',
            jurisdiction='Health-related legislation',
            chairperson=self.user,
            established_date=date.today()
        )
        self.assertEqual(str(committee), 'COH')
        
    def test_committee_membership(self):
        committee = Committee.objects.create(
            name='Committee on Health',
            committee_type='standing',
            jurisdiction='Health-related legislation',
            established_date=date.today()
        )
        
        membership = CommitteeMembership.objects.create(
            committee=committee,
            member=self.user,
            role='chairperson',
            start_date=date.today()
        )
        
        self.assertEqual(committee.memberships.count(), 1)
        self.assertEqual(committee.member_count, 1)


class OversightActivityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_create_oversight_activity(self):
        activity = OversightActivity.objects.create(
            title='DOH Budget Review',
            activity_type='audit',
            description='Review of DOH budget implementation',
            target_agency='Department of Health',
            lead_member=self.user,
            status='planned',
            start_date=date.today()
        )
        self.assertEqual(str(activity), 'Audit Review: DOH Budget Review')
        
    def test_is_overdue(self):
        activity = OversightActivity.objects.create(
            title='Test Activity',
            activity_type='audit',
            description='Test description',
            target_agency='Test Agency',
            status='ongoing',
            start_date=date.today() - timedelta(days=30),
            requires_followup=True,
            followup_deadline=date.today() - timedelta(days=5)
        )
        self.assertTrue(activity.is_overdue)


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.session = LegislativeSession.objects.create(
            session_number='First Regular',
            congress_number='19th',
            start_date=date.today(),
            is_current=True
        )
        
    def test_dashboard_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('parliamentary:dashboard'))
        self.assertEqual(response.status_code, 200)
        
    def test_measure_list_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('parliamentary:measure_list'))
        self.assertEqual(response.status_code, 200)
        
    def test_measure_create_requires_login(self):
        response = self.client.get(reverse('parliamentary:measure_create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_measure_create_post(self):
        self.client.login(username='testuser', password='testpass123')
        data = {
            'session': self.session.id,
            'measure_type': 'bill',
            'number': 'HB 5678',
            'title': 'Test Bill',
            'abstract': 'Test abstract',
            'priority': 'normal'
        }
        response = self.client.post(reverse('parliamentary:measure_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(LegislativeMeasure.objects.filter(number='HB 5678').exists())