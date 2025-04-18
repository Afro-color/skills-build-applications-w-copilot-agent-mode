import os
from decouple import config

# Add this at the top of the file to define BASE_DIR
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ensure django_heroku is installed
try:
    import django_heroku
except ImportError:
    raise ImportError("django_heroku module is not installed. Please install it using 'pip install django-heroku'.")

import dj_database_url

# Ensure all critical environment variables are loaded
from dotenv import load_dotenv
load_dotenv()

# Utility function to fetch environment variables with fallback values
def get_env_variable(var_name, default_value):
    """Fetch an environment variable with a fallback value."""
    return os.getenv(var_name, default_value)

# Update DATABASES configuration to use DATABASE_URL for production
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", "sqlite:///db.sqlite3"),
        conn_max_age=600,
        ssl_require=True if os.getenv("ENVIRONMENT") == "production" else False,
    )
}

# Ensure a default value for CERT_FILE
CERT_FILE = os.getenv('CERT_FILE', 'default_cert_file_path')

# Add fallback values for required environment variables
CERT_FILE = get_env_variable("CERT_FILE", "path/to/default/certificate.crt")
KEY_FILE = get_env_variable("KEY_FILE", "path/to/default/private.key")

# Debugging log to verify CERT_FILE
print(f"CERT_FILE: {CERT_FILE}")

# Ensure other critical environment variables have defaults
SECRET_KEY = get_env_variable("SECRET_KEY", "default-secret-key")
DEBUG = get_env_variable("DEBUG", "True") == "True"

# Configure Redis for Celery
CELERY_BROKER_URL = get_env_variable("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# Add Whitenoise for static file management
MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # ...existing middleware...
]

# Configure static files for Heroku
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Add logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# Debugging log to verify environment variables
print(f"CERT_FILE: {CERT_FILE}")
print(f"SECRET_KEY: {SECRET_KEY}")
print(f"DEBUG: {DEBUG}")
print(f"DATABASE_URL: {DATABASE_URL}")
print(f"REDIS_URL: {REDIS_URL}")

# Use django-heroku for Heroku-specific settings
django_heroku.settings(locals())
