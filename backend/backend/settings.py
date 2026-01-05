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
    'users',
    'organizations',
    'projects',
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

CREATE_ORGANIZATION = 'organizations.functions.create_organization'
SAVE_USER = 'users.functions.save_user'
POST_PROCESS_REIMPORT = 'core.utils.common.empty'
USER_SERIALIZER = 'users.serializers.BaseUserSerializer'
WHOAMI_USER_SERIALIZER = 'users.serializers.BaseWhoAmIUserSerializer'
USER_SERIALIZER_UPDATE = 'users.serializers.BaseUserSerializerUpdate'
TASK_SERIALIZER = 'tasks.serializers.BaseTaskSerializer'
EXPORT_DATA_SERIALIZER = 'data_export.serializers.BaseExportDataSerializer'
DATA_MANAGER_GET_ALL_COLUMNS = 'data_manager.functions.get_all_columns'
DATA_MANAGER_ANNOTATIONS_MAP = {}
DATA_MANAGER_ACTIONS = {}
DATA_MANAGER_CUSTOM_FILTER_EXPRESSIONS = 'data_manager.functions.custom_filter_expressions'
DATA_MANAGER_PREPROCESS_FILTER = 'data_manager.functions.preprocess_filter'
DATA_MANAGER_CHECK_ACTION_PERMISSION = 'data_manager.actions.check_action_permission'
BULK_UPDATE_IS_LABELED = 'tasks.functions.bulk_update_is_labeled_by_overlap'
USER_LOGIN_FORM = 'users.forms.LoginForm'
PROJECT_MIXIN = 'projects.mixins.ProjectMixin'
TASK_MIXIN = 'tasks.mixins.TaskMixin'
LSE_PROJECT = None
GET_TASKS_AGREEMENT_QUERYSET = None
SHOULD_ATTEMPT_GROUND_TRUTH_FIRST = None
ANNOTATION_MIXIN = 'tasks.mixins.AnnotationMixin'
ORGANIZATION_MIXIN = 'organizations.mixins.OrganizationMixin'
USER_MIXIN = 'users.mixins.UserMixin'
ORGANIZATION_MEMBER_MIXIN = 'organizations.mixins.OrganizationMemberMixin'
MEMBER_PERM = 'core.api_permissions.MemberHasOwnerPermission'
RECALCULATE_ALL_STATS = None
GET_STORAGE_LIST = 'io_storages.functions.get_storage_list'
STORAGE_LOAD_TASKS_JSON = 'io_storages.utils.load_tasks_json_lso'
STORAGE_ANNOTATION_SERIALIZER = 'io_storages.serializers.StorageAnnotationSerializer'
TASK_SERIALIZER_BULK = 'tasks.serializers.BaseTaskSerializerBulk'
PREPROCESS_FIELD_NAME = 'data_manager.functions.preprocess_field_name'
INTERACTIVE_DATA_SERIALIZER = 'data_export.serializers.BaseExportDataSerializerForInteractive'
PROJECT_IMPORT_PERMISSION = 'projects.permissions.ProjectImportPermission'
DELETE_TASKS_ANNOTATIONS_POSTPROCESS = None
PROJECT_SAVE_DIMENSIONS_POSTPROCESS = None
FEATURE_FLAGS_GET_USER_REPR = 'core.feature_flags.utils.get_user_repr'
FEATURE_FLAGS_GET_USER_REPR_FROM_ORGANIZATION = 'core.feature_flags.utils.get_user_repr_from_organization'

# Test factories
ORGANIZATION_FACTORY = 'organizations.tests.factories.OrganizationFactory'
PROJECT_FACTORY = 'projects.tests.factories.ProjectFactory'
USER_FACTORY = 'users.tests.factories.UserFactory'

# Feature Flags
FEATURE_FLAGS_API_KEY = 'any key'

# we may set feature flags from file
FEATURE_FLAGS_FROM_FILE = False
FEATURE_FLAGS_FILE = 'feature_flags.json'
# or if file is not set, default is using offline mode
FEATURE_FLAGS_OFFLINE = True
# default value for feature flags (if not overridden by environment or client)
FEATURE_FLAGS_DEFAULT_VALUE = False
