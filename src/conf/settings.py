from datetime import timedelta
from pathlib import Path

import environ

env = environ.Env(
    DEBUG=(bool, True),
    SECRET_KEY=(str, 'very secret key'),
    ENV_NAME=(str, 'local'),
    RUN_TASKS_LOCAL=(bool, True),
    BEAUTY_ADMIN=(bool, True),
)
env.read_env()

BASE_DIR = Path(__file__).parents[1]

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')

ROOT_URLCONF = 'conf.urls'
WSGI_APPLICATION = 'conf.wsgi.application'
ASGI_APPLICATION = 'conf.asgi.application'

CONSTANCE_CONFIG = {}
CONSTANCE_IGNORE_ADMIN_VERSION_CHECK = True
CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_extensions',
    'django_filters',
    'autocompletefilter',
    'django_object_actions',
    'django_json_widget',
    'reversion',
    'rest_framework',
    'drf_spectacular',
    'corsheaders',

    'django_celery_results',
    'django_celery_beat',

    'loginas',
    'debug_toolbar',

    'constance',
    'constance.backends.database',

    'health_check',
    'health_check.db',

    'apps.user',
    'apps.main',
]
if env('BEAUTY_ADMIN'):
    INSTALLED_APPS.insert(0, 'jet')

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'utils.middlewares.DisableCSRF',  # todo: починить
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates', BASE_DIR / 'apps/main/static/'],
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

DATABASES = {
    'default': env.db(default='sqlite:///db.sqlite3'),
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CACHES = {
    'default': env.cache(default='locmemcache://'),
}

ALLOWED_HOSTS = ['*']
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
CORS_ORIGIN_ALLOW_ALL = True
X_FRAME_OPTIONS = 'SAMEORIGIN'

INTERNAL_IPS = [
    '127.0.0.1',
]

if DEBUG:
    AUTH_PASSWORD_VALIDATORS = []
else:
    AUTH_PASSWORD_VALIDATORS = [
        {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
        {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
        {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
        {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    ]

AUTH_USER_MODEL = 'user.CustomUser'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'apps.user.auth_backend.CustomAuthBackend',
]
LOGIN_REDIRECT_URL = '/api/v1/'


LANGUAGE_CODE = 'ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/_storage/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = '_storage'

REST_FRAMEWORK = {
    'NON_FIELD_ERRORS_KEY': 'non_field_errors',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.DjangoObjectPermissions',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'utils.renderers.JsonUnicodeRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'PAGE_SIZE': 100,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

SPECTACULAR_SETTINGS = {
    'SCHEMA_PATH_PREFIX': '/api/v[0-9]',
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(weeks=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,

    'AUTH_HEADER_TYPES': ('Bearer', 'Token'),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

ENV_NAME = env('ENV_NAME')
if ENV_NAME == 'local':
    CELERY_BROKER_URL = env.str('BROKER_URL', None)
else:
    CELERY_BROKER_URL = env.str('BROKER_URL')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_TASK_ALWAYS_EAGER = env('RUN_TASKS_LOCAL')
