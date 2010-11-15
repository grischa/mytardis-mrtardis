import logging
from os import path

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = ':memory:'
ROOT_URLCONF = 'tardis.urls'
DEBUG = True
STATIC_DOC_ROOT = path.join(path.abspath(path.dirname(__file__)),
                            'tardis_portal/site_media')

# LDAP configuration
LDAP_ENABLE = False

FILE_STORE_PATH = path.abspath(path.join(path.dirname(__file__),
    '../var/store/'))
STAGING_PATH = path.abspath(path.join(path.dirname(__file__),
    "../var/staging/"))

ADMIN_MEDIA_STATIC_DOC_ROOT = ''
HANDLEURL = ''
SITE_ID = '1'
MEDIA_URL = '/site_media/'
TEMPLATE_DIRS = ['.']
#TEMPLATE_DIRS = ['.', 'tardis_portal/']

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tardis.tardis_portal.minidetector.Middleware')

INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.admin',
        'django.contrib.admindocs',
        'django_extensions',
        'tardis.tardis_portal',
        'registration',
        'tardis.tardis_portal.templatetags',
        'django_nose',
        )

TEST_RUNNER = 'django_nose.run_tests'

LOG_FILENAME = '/dev/stderr'

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# logging levels are: DEBUG, INFO, WARN, ERROR, CRITICAL
LOG_LEVEL = logging.DEBUG
