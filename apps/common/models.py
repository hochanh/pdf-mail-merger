from django.db import models


class SignalSaveMixin(object):

    def save_without_signals(self, *args, **kwargs):
        self._disable_signals = True
        self.save(*args, **kwargs)
        self._disable_signals = False


class TimestampModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        editable=False,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        editable=False,
    )

    class Meta:
        abstract = True
