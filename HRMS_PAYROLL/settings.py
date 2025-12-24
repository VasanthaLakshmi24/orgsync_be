# settings.py
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta
from celery.schedules import crontab
load_dotenv()
# apiurl=os.environ.get('apiurl')

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

print("========== ENV DEBUG ==========")
print("BASE_DIR:", BASE_DIR)
print("ENV_PATH:", ENV_PATH)
print("ENV EXISTS:", ENV_PATH.exists())
print("================================")

load_dotenv(ENV_PATH)
load_dotenv(os.path.join(BASE_DIR, ".env"))
temp_dir=os.path.join(BASE_DIR,'templates')

DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000000
SECRET_KEY = 'django-insecure-u8cn!ri2su@vpb897pb#78w2*i!1rd0maeh43&^l2+j$j65^mk'

DEBUG = True

ALLOWED_HOSTS = ['*']


USE_TZ = True
TIME_ZONE = 'Asia/Kolkata'

INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'payrollapp',
    'rest_framework',
    'rest_framework_simplejwt',
    'django_celery_results',
    'django_celery_beat',
    'import_export',
    # 'activity_log',
    'cloudinary',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'activity_log.middleware.ActivityLogMiddleware',
]

JWT_ALGORITHM = 'HS256'

CSRF_TRUSTED_ORIGINS = ['https://hrms-backend-9of6.onrender.com']

CORS_ALLOW_HEADERS = ['*']

CORS_ALLOW_ALL_ORIGINS = True

# CORS_ALLOWED_ORIGINS = [
#     apiurl,
#     "https://www.gaorgsync.com",
# ]

# CORS_ORIGIN_WHITELIST = [apiurl,'https://www.gaorgsync.com',]
# CORS_TRUSTED_ORIGINS = [apiurl,'https://www.gaorgsync.com',]
# ===================== CORS CONFIG (FIXED) =====================

CORS_ALLOW_ALL_ORIGINS = True  # safe for dev

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://www.gaorgsync.com",
    "https://hrms-backend-9of6.onrender.com",
]

CORS_ALLOW_HEADERS = ['*']


ROOT_URLCONF = 'HRMS_PAYROLL.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [temp_dir],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'HRMS_PAYROLL.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

# DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': BASE_DIR / 'db.sqlite3',
#    }
# }


# DATABASE_ROUTERS = ['activity_log.router.DatabaseAppsRouter']
# DATABASE_APPS_MAPPING = {'activity_log': 'default'}

# ACTIVITYLOG_AUTOCREATE_DB = False

import dj_database_url

DATABASES = {
     'default': {
         'ENGINE': 'django.db.backends.postgresql_psycopg2',
         'NAME': os.environ.get('DB_NAME'),
         'USER': os.environ.get('DB_USER'),
         'PASSWORD': os.environ.get('DB_PASSWORD'),
         'HOST': os.environ.get('DB_HOST'),
         'PORT': os.environ.get('DB_PORT'),
     }
}

# DATABASES = {
#     'default': dj_database_url.config(
#         default=os.environ.get('DATABASE_URL')
#     )
# }

PDFKIT_CONFIG = {
    'wkhtmltopdf': ('/usr/bin/wkhtmltopdf'),
    # 'wkhtmltopdf': (os.path.join(BASE_DIR, 'wkhtmltopdf.exe')),
    'options': {
        'page-size': 'A4',
        'encoding': 'UTF-8',
        'no-outline': None,
        'quiet': ''
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/images/'

# CLOUDINARY = {
#     'cloud_name': os.environ.get('cloud_name'),
#     'api_key': os.environ.get('api_key'),
#     'api_secret': os.environ.get('api_secret'),
# }

MEDIA_ROOT = os.path.join(BASE_DIR, 'images/')

AUTH_USER_MODEL = 'payrollapp.User'

AUTHENTICATION_BACKENDS = [
    'payrollapp.backends.CustomUserAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7), 
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30), 
    'AUTH_HEADER_TYPES': ('Bearer')
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get('EMAIL_ID')  
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = "smtp.gmail.com"
# EMAIL_PORT = 587
# EMAIL_HOST_USER = os.environ.get('EMAIL_ID')  
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
# EMAIL_USE_TLS = True
# EMAIL_USE_SSL = False
# DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_ID')


accept_content = ['application/json']
result_serializer = 'json'
task_serializer = 'json'



result_backend = 'django-db'
url=os.environ.get('DATABASE_URL')




# Celery beat
# CELERY_TASK_TIME_LIMIT = 3000
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'
CELERY_TIMEZONE = "Asia/Kolkata"
# CELERY_TASK_TRACK_STARTED = True
# # CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
# CELERY_TASK_TIME_LIMIT = 30 * 60
# ================= CERTIFICATION EXPIRY SCHEDULER =================

# CELERY_BEAT_SCHEDULE = {
#     "certification-expiry-notification-daily": {
#         "task": "payrollapp.tasks.certification_expiry_notification",
#         "schedule": crontab(hour=9, minute=0),  # runs daily at 9 AM
#     }
# }


RAZOR_KEY_ID = os.environ.get('RAZOR_KEY_ID')
RAZOR_KEY_SECRET = os.environ.get('RAZOR_KEY_SECRET')
MAILCHIMP_LIST_ID='3592fd91ff'
MAILCHIMP_API_KEY = '9e20cce96031af71d953c93afdc7c369-us177'
MAILCHIMP_API_URL = 'https://us17.api.mailchimp.com/3.0/'

MAILCHIMP_REGION = 'us17'
MAILCHIMP_SERVER_PREFIX='us17'
MAILCHIMP_DATA_CENTER='us17'
MAILCHIMP_FROM_EMAIL='gaorgsync@gmail.com'
MAILCHIMP_FROM_NAME='Venkateswara Rao'

import base64

key_base64 = '3F7PpLGo7ZcbKH4xZHYyMmbA0W3gGtKwzO2v34p2FhY='
ENCRYPTION_KEY = base64.b64decode(key_base64)
REDIS_HOST = "192.168.0.107"
REDIS_PORT = "6380"

REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# Celery broker + backend
CELERY_BROKER_URL = 'redis://localhost:6380/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6380/0'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Django Cache using Redis
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

