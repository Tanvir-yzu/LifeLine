import os

from .local_settings import (
    SECRET_KEY, DEBUG, ALLOWED_HOSTS, DB_CONFIG,
    TEMPLATES_DIR, STATICFILES_DIR, STATIC_DIR, MEDIA_DIR, LOGS_DIR, EMAIL_USER, EMAIL_PASSWORD, DEFAULT_EMAIL, 
)
from LifeLine.logging import LOGGING

# Build paths inside the project like this: os.path.join(BASE_DIR, 'subdir')
SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SETTINGS_DIR)
TEMPLATES_DIR = os.getenv('TEMPLATES_DIR', TEMPLATES_DIR)
STATICFILES_DIR = os.getenv('STATICFILES_DIR', STATICFILES_DIR)

STATIC_DIR = os.getenv('STATIC_DIR', STATIC_DIR)
MEDIA_DIR = os.getenv('MEDIA_DIR', MEDIA_DIR)
LOGS_DIR = os.getenv('LOGS_DIR', LOGS_DIR)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = DEBUG

ALLOWED_HOSTS = ALLOWED_HOSTS


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_extensions',
    'bloodhome',
    'users',
    'donations',
    'adminhome',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'LifeLine.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'LifeLine.wsgi.application'

AUTH_USER_MODEL = 'users.User'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# Database
DATABASES = {
    'default': DB_CONFIG
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = STATIC_DIR  # production, don't forget to run collectstatic
STATICFILES_DIRS = [STATICFILES_DIR]  # development environment

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = MEDIA_DIR

SITE_ID = 1
DOMAIN_NAME = 'localhost:8000'



# Email settings for Gmail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Gmail's SMTP server
EMAIL_PORT = 587  # Port for TLS
EMAIL_USE_TLS = True  # Use TLS encryption
EMAIL_HOST_USER = EMAIL_USER  # Your Gmail address
EMAIL_HOST_PASSWORD = EMAIL_PASSWORD  # Your Gmail password or App Password  
DEFAULT_FROM_EMAIL = DEFAULT_EMAIL  # Default sender email

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Logging Configuration
if os.getenv('DISABLE_LOGGING', False):  # for celery in jenkins ci only
    LOGGING_CONFIG = None
LOGGING = LOGGING



# Jazzmin configuration
JAZZMIN_SETTINGS = {
    "site_title": "LifeLine Blood Bank",
    "site_header": "LifeLine Administration",
    "site_brand": "LifeLine",
    "site_logo": None,
    "login_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    "welcome_sign": "Welcome to LifeLine Blood Bank Administration",
    "copyright": "LifeLine Blood Bank",
    "search_model": ["users.User", "users.BloodRequest"],
    "user_avatar": None,
    
    # Top Menu
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "users.User"},
    ],
    
    # User Menu
    "usermenu_links": [
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "users.User"}
    ],
    
    # Side Menu
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    
    # Custom CSS/JS
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"users.user": "collapsible", "users.bloodrequest": "vertical_tabs"},
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-teal",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-info",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}
