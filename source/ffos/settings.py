#-*- coding: utf-8 -*-
"""
Django settings for ffos project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

TESTING = 'test' in sys.argv
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '(b*v9gk(w^p*%qn1lk2+h7bjg7=(arvy=xu06ahjl9&&@_(_j1'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_nose',
# Tastypie looks like a very good rest api framework, but for now just simple views
    'tastypie',
    'ffos',
    'ffos.recommender',
    'ffos.gui',
    'debug_toolbar',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    #'django.middleware.cache.UpdateCacheMiddleware',
    #'django.middleware.cache.FetchFromCacheMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'ffos.urls'

WSGI_APPLICATION = 'ffos.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

import socket
HOSTS = {
    'chronos': '192.168.188.128',
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'raqksixq_ffosv1',
        'USER': 'raqksixq_frappe',
        'PASSWORD': 'Sp21o61H4',
        'HOST': HOSTS[socket.gethostname()] if socket.gethostname() in HOSTS
            else 'localhost',
    } if not TESTING else {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'raqksixq_ffosv1',
        'CHARSET': 'utf8',
        'TEST_NAME': 'test_ffosv1',
        'TEST_CHARSET': 'utf8',
        'USER': 'root',
        'PASSWORD': 'Sp21o61H4',
        'HOST': HOSTS[socket.gethostname()] if socket.gethostname() in HOSTS
            else 'localhost',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-en'

TIME_ZONE = 'Europe/Madrid'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

# Logging

import logging
from datetime import datetime

FORMAT = '%(asctime)-15s: %(message)s'
path = os.path.dirname(__file__)
logging.basicConfig(format=FORMAT,level=logging.DEBUG if DEBUG else \
logging.WARNING,filename=datetime.now().strftime(path+
    '/logs/%d-%m-%Y %H:%M.log')
    if DEBUG else datetime.now().strftime(path+'/logs/%d-%m-%Y.log')
)

# Testing
# Nose settings

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
DEBUG_TOOLBAR_PATCH_SETTINGS = DEBUG

# Caching

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        #'LOCATION': '/var/tmp/django_cache',
        'TIMEOUT': 60,
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}
