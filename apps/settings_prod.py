import os

from .settings import *  # NOQA

DEBUG = False
ALLOWED_HOSTS = '*'

# AWS settings
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise Exception("SECRET_KEY is required")

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN')
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
AWS_DEFAULT_ACL = 'public-read'

DEFAULT_FILE_STORAGE = 'apps.common.storages.MediaRootS3BotoStorage'
STATICFILES_STORAGE = 'apps.common.storages.StaticRootS3BotoStorage'
