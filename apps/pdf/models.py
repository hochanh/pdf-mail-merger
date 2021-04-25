import copy
import string
import uuid

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.crypto import get_random_string


def cachedfile_name(instance, filename: str) -> str:
    secret = get_random_string(length=16, allowed_chars=string.ascii_letters + string.digits)
    return 'cache/%s/%s.%s' % (instance.id, secret, filename.split('.')[-1])


class CachedFile(models.Model):
    """
    An uploaded file, with an optional expiry date.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    expires = models.DateTimeField(null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    filename = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    file = models.FileField(null=True, blank=True, upload_to=cachedfile_name)


@receiver(post_delete, sender=CachedFile)
def cached_file_delete(sender, instance, **kwargs):
    if instance.file:
        # Pass false so FileField doesn't save the model.
        instance.file.delete(False)


def modelcopy(obj: models.Model):
    n = obj.__class__()
    for f in obj._meta.fields:
        val = getattr(obj, f.name)
        if isinstance(val, models.Model):
            setattr(n, f.name, copy.copy(val))
        else:
            setattr(n, f.name, copy.deepcopy(val))
    return n
