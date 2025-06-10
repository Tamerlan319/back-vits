from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class YandexMediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    default_acl = 'public-read'

class PrivateMediaStorage(S3Boto3Storage):
    bucket_name = settings.PRIVATE_AWS_STORAGE_BUCKET_NAME
    default_acl = settings.PRIVATE_AWS_DEFAULT_ACL
    querystring_auth = settings.PRIVATE_AWS_QUERYSTRING_AUTH
    location = settings.PRIVATE_MEDIA_LOCATION
    file_overwrite = False