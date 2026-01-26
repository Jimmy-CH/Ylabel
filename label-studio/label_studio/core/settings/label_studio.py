import yaml
from core.settings.base import *  # noqa


ENVIRONMENT = os.environ.get('DJANGO_ENV', 'dev')
CONFIG_FILE = os.path.join(BASE_DIR, 'configs', 'config.yml')


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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'USER': env_config.get('postgre_user', 'postgres'),
        'PASSWORD': env_config.get('postgre_password', '4432chen'),
        'NAME': env_config.get('postgre_name', 'label_studio'),
        'HOST': env_config.get('postgre_host', 'localhost'),
        'PORT': int(env_config.get('postgre_port', '5432')),
        # 本地测试
        # 'ENGINE': 'django.db.backends.postgresql',
        # 'USER': 'postgres',
        # 'PASSWORD': '4432chen',
        # 'NAME': 'labelstudio1',
        # 'HOST': 'localhost',
        # 'PORT': 5432,
    },
}
# RQ
RQ_QUEUES = {
    'critical': {
        'HOST': env_config.get('redis_host', 'localhost'),
        'PORT': env_config.get('redis_port', 6379),
        'DB': env_config.get('redis_db', 12),
        'DEFAULT_TIMEOUT': 180,
        'PASSWORD': env_config.get('redis_password', '')
    },
    'high': {
        'HOST': env_config.get('redis_host', 'localhost'),
        'PORT': env_config.get('redis_port', 6379),
        'DB': env_config.get('redis_db', 12),
        'DEFAULT_TIMEOUT': 180,
        'PASSWORD': env_config.get('redis_password', '')
    },
    'default': {
        'HOST': env_config.get('redis_host', 'localhost'),
        'PORT': env_config.get('redis_port', 6379),
        'DB': env_config.get('redis_db', 12),
        'DEFAULT_TIMEOUT': 180,
        'PASSWORD': env_config.get('redis_password', '')
    },
    'low': {
        'HOST': env_config.get('redis_host', 'localhost'),
        'PORT': env_config.get('redis_port', 6379),
        'DB': env_config.get('redis_db', 12),
        'DEFAULT_TIMEOUT': 180,
        'PASSWORD': env_config.get('redis_password', '')
    },
}

MIDDLEWARE.append('organizations.middleware.DummyGetSessionMiddleware')
MIDDLEWARE.append('core.middleware.UpdateLastActivityMiddleware')
if INACTIVITY_SESSION_TIMEOUT_ENABLED:
    MIDDLEWARE.append('core.middleware.InactivitySessionTimeoutMiddleWare')

ADD_DEFAULT_ML_BACKENDS = False

LOGGING['root']['level'] = get_env('LOG_LEVEL', 'WARNING')

DEBUG_PROPAGATE_EXCEPTIONS = get_bool_env('DEBUG_PROPAGATE_EXCEPTIONS', False)

SESSION_COOKIE_SECURE = get_bool_env('SESSION_COOKIE_SECURE', False)

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

SENTRY_DSN = ""
SENTRY_ENVIRONMENT = get_env('SENTRY_ENVIRONMENT', 'opensource')

FRONTEND_SENTRY_DSN = get_env(
    'FRONTEND_SENTRY_DSN', 'https://5f51920ff82a4675a495870244869c6b@o227124.ingest.sentry.io/5838868'
)
FRONTEND_SENTRY_ENVIRONMENT = get_env('FRONTEND_SENTRY_ENVIRONMENT', 'opensource')

EDITOR_KEYMAP = json.dumps(get_env('EDITOR_KEYMAP'))

from label_studio import __version__
from label_studio.core.utils import sentry

sentry.init_sentry(release_name='label-studio', release_version=__version__)

# we should do it after sentry init
from label_studio.core.utils.common import collect_versions

versions = collect_versions()

# in Label Studio Community version, feature flags are always ON
FEATURE_FLAGS_DEFAULT_VALUE = True
# or if file is not set, default is using offline mode
FEATURE_FLAGS_OFFLINE = get_bool_env('FEATURE_FLAGS_OFFLINE', True)

FEATURE_FLAGS_FILE = get_env('FEATURE_FLAGS_FILE', 'feature_flags.json')
FEATURE_FLAGS_FROM_FILE = True
try:
    from core.utils.io import find_node

    find_node('label_studio', FEATURE_FLAGS_FILE, 'file')
except IOError:
    FEATURE_FLAGS_FROM_FILE = False

STORAGE_PERSISTENCE = get_bool_env('STORAGE_PERSISTENCE', True)
