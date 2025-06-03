"""
Development settings for #FahanieCares project.
"""

import os
from dotenv import load_dotenv
from .base import *

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Database configuration
# Use PostgreSQL if configured, otherwise fall back to SQLite
if os.getenv('DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'fahanie_cares_dev'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    # Fall back to SQLite if PostgreSQL not configured
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Add development specific apps
INSTALLED_APPS += [
    # 'django_extensions',  # Commented out for now
]

# Development-specific middleware
MIDDLEWARE += [
    # Add any development-specific middleware here
]

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Notion API settings
NOTION_API_KEY = os.getenv('NOTION_API_KEY', '')
NOTION_MEMBER_DATABASE = os.getenv('NOTION_MEMBER_DATABASE', '')
NOTION_PROGRAM_DATABASE = os.getenv('NOTION_PROGRAM_DATABASE', '')
NOTION_REQUEST_DATABASE = os.getenv('NOTION_REQUEST_DATABASE', '')
NOTION_CHAPTER_DATABASE = os.getenv('NOTION_CHAPTER_DATABASE', '')
NOTION_MINISTRY_DATABASE = os.getenv('NOTION_MINISTRY_DATABASE', '')

# Development-specific logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}