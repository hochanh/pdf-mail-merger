from storages.backends.s3boto3 import S3Boto3Storage, S3ManifestStaticStorage


class MediaRootS3BotoStorage(S3Boto3Storage):
    location = 'media'


class StaticRootS3BotoStorage(S3ManifestStaticStorage):
    location = 'static'
