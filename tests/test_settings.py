"""
Test settings for #FahanieCares project.
"""

from config.settings.base import *

# Override settings for testing
DEBUG = False
TESTING = True

# Use in-memory database for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Speed up password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable rate limiting for tests
RATE_LIMIT_PER_MINUTE = 10000
MAX_LOGIN_ATTEMPTS = 100

# Test email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Static files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Media files for testing
MEDIA_ROOT = os.path.join(BASE_DIR, 'test_media')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
        'level': 'DEBUG',
    },
}

# Notion test settings
NOTION_API_KEY = 'test_api_key'
NOTION_CONSTITUENT_DATABASE = 'test_constituent_db'
NOTION_SERVICE_APPLICATION_DB_ID = 'test_service_db'
NOTION_CHAPTER_DATABASE = 'test_chapter_db'