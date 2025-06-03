# #FahanieCares Digital Platform

The official website and constituent management system for MP Atty. Sittie Fahanie S. Uy-Oyod's public service initiative.

## Overview

The #FahanieCares platform is a comprehensive digital solution that connects constituents with government services through an efficient referral system. Built with Django and integrated with Notion as the primary database, the system supports the mission of "Bringing Public Service Closer to You."

## Features

- **Constituent Management**: Complete profile management for district constituents
- **Service Referral System**: Streamlined process for connecting constituents with government services
- **Chapter Management**: Organize and coordinate #FahanieCares chapters across municipalities
- **Direct Service Programs**: Manage assistance programs and track beneficiaries
- **Parliamentary Work Tracking**: Document and share legislative activities
- **Mobile-Responsive Design**: Field-ready interface for community outreach
- **Offline Capability**: PWA features for areas with limited connectivity
- **Multi-Factor Authentication**: Enhanced security for staff accounts

## Technology Stack

- **Backend**: Django 4.2+ with Python 3.9+
- **Database**: Notion API (primary), PostgreSQL (production), SQLite (development)
- **Frontend**: Django Templates with TailwindCSS
- **Authentication**: Django Auth with MFA support
- **Infrastructure**: AWS (EC2, S3, CloudFront)
- **Containerization**: Docker with docker-compose

## Installation

### Prerequisites

- Python 3.9 or higher
- Node.js 14+ (for TailwindCSS)
- Git
- Docker (optional, for containerized deployment)

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/fahanie-cares/fahanie-cares-django.git
cd fahanie-cares-django
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
NOTION_API_KEY=your-notion-api-key
NOTION_CONSTITUENT_DATABASE=database-id
NOTION_SERVICE_DATABASE=database-id
# Add other Notion database IDs as needed
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Load sample data (optional):
```bash
python create_sample_data.py
```

8. Compile TailwindCSS:
```bash
npm install
npm run build:css
```

9. Start the development server:
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## Testing

Run the test suite:

```bash
# All tests
python manage.py test

# Specific app tests
python manage.py test apps.referrals

# With coverage
coverage run --source='.' manage.py test
coverage report
```

## Deployment

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t fahaniecares .
```

2. Run with docker-compose:
```bash
docker-compose up -d
```

### AWS Deployment

1. Configure AWS credentials:
```bash
aws configure
```

2. Run deployment script:
```bash
./deployment/deploy.sh
```

## Project Structure

```
fahanie_cares_django/
├── apps/                   # Django applications
│   ├── core/              # Core functionality
│   ├── users/             # User authentication and profiles
│   ├── constituents/      # Constituent management
│   ├── referrals/         # Service referral system
│   ├── chapters/          # Chapter organization
│   └── services/          # Direct service programs
├── config/                # Django configuration
│   ├── settings/          # Environment-specific settings
│   ├── urls.py           # URL configuration
│   └── wsgi.py           # WSGI configuration
├── templates/             # HTML templates
├── static/               # Static files (CSS, JS, images)
├── media/                # User-uploaded files
├── utils/                # Utility modules
│   └── notion/           # Notion API integration
├── tests/                # Test modules
└── deployment/           # Deployment configurations
```

## Security

- Multi-factor authentication required for staff accounts
- Session timeout after 30 minutes of inactivity
- Rate limiting on API endpoints
- CSRF protection on all forms
- Content Security Policy headers
- File upload validation and virus scanning

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Development Guidelines

- Follow PEP 8 coding standards
- Write tests for new features
- Update documentation for API changes
- Use conventional commit messages
- Ensure mobile responsiveness
- Consider offline functionality

## License

This project is proprietary software. All rights reserved.

## Support

For technical support or questions:
- Email: tech@fahaniecares.ph
- Issue Tracker: GitHub Issues

## Acknowledgments

- Built for the Office of MP Atty. Sittie Fahanie S. Uy-Oyod
- Powered by Django and Notion API
- Supported by the #FahanieCares team