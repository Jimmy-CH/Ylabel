"""
Django settings for backend project.
"""

import os
import yaml
import platform
from pathlib import Path
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


ENVIRONMENT = os.environ.get('DJANGO_ENV', 'development')


CONFIG_FILE = BASE_DIR / 'configs/config.yml'


def load_yaml_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise ImproperlyConfigured(f"Config file {CONFIG_FILE} not found.")
    except yaml.YAMLError as e:
        raise ImproperlyConfigured(f"Error parsing YAML config: {e}")


config_data = load_yaml_config()
try:
    env_config = config_data[ENVIRONMENT]
except KeyError:
    raise ImproperlyConfigured(f"Environment '{ENVIRONMENT}' not found in config.yml.")

SECRET_KEY = env_config['secret_key']
DEBUG = env_config['debug']
print(f"Current Environment: {ENVIRONMENT}")

DATABASES = {
    'default': {
        'ENGINE': env_config['database']['engine'],
        'NAME': env_config['database']['name'],
        'USER': env_config['database']['user'],
        'PASSWORD': env_config['database']['password'],
        'HOST': env_config['database']['host'],
        'PORT': env_config['database']['port'],
        'OPTIONS': env_config['database'].get('options', {}),    # 可选配置
    }
}

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rules',
    'users',
    'organizations',
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

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'backend.wsgi.application'

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


STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 媒体文件配置
MEDIA_URL = '/media/'
if platform.system().lower() == 'windows':
    MEDIA_ROOT = r'D:/media/'
    DB_BACKUP_PATH = r'D:/media/backups/mysql/'
    LOG_PATH = BASE_DIR / 'logs'
else:
    # 项目根目录下的 media/ 文件夹
    MEDIA_ROOT = BASE_DIR / 'media'
    DB_BACKUP_PATH = '/opt/backups/mysql/'
    LOG_PATH = '/opt/app/logs/'

os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(DB_BACKUP_PATH, exist_ok=True)
os.makedirs(LOG_PATH, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_PATH, 'django.log'),
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        }
    },
    'root': {
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'] if DEBUG else [],  # 生产环境完全关闭 console 输出
            'level': 'INFO' if DEBUG else 'WARNING',
            'propagate': False,
        },
        'label': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# OSS version does not support Redis
REDIS_ENABLED = False

# Auth modules
AUTH_USER_MODEL = 'users.User'

ORGANIZATION_MIXIN = 'organizations.mixins.OrganizationMixin'
USER_MIXIN = 'users.mixins.UserMixin'
ORGANIZATION_MEMBER_MIXIN = 'organizations.mixins.OrganizationMemberMixin'

