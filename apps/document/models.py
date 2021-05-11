import string
from collections import OrderedDict
from io import TextIOWrapper

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from tablib import Dataset

from apps.account.models import Account, User
from apps.common.models import TimestampModel

DEFAULT_BACKGROUND = 'pdf/blank_a4.pdf'


def bg_name(instance, filename: str) -> str:
    secret = get_random_string(length=16, allowed_chars=string.ascii_letters + string.digits)

    return 'background/{id}/{secret}.pdf'.format(
        id=instance.user_id,
        secret=secret
    )


def data_name(instance, filename: str) -> str:
    secret = get_random_string(length=16, allowed_chars=string.ascii_letters + string.digits)
    return 'data/{id}/{secret}.{ext}'.format(
        id=instance.user_id,
        secret=secret,
        ext=filename.split('.')[-1],
    )


class Document(TimestampModel, models.Model):
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    name = models.CharField(max_length=256, verbose_name=_('Name'))

    headers = models.JSONField(default=list, editable=False)
    first_row = models.JSONField(default=dict, editable=False)

    file = models.FileField(upload_to=data_name, max_length=255,
                            validators=[FileExtensionValidator(allowed_extensions=['csv', 'xls', 'xlsx'])])

    layout = models.JSONField(default=list)
    background = models.FileField(null=True, blank=True, upload_to=bg_name, max_length=255)

    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, editable=False)

    def get_variables(self):
        return OrderedDict(
            (header, {
                "label": header,
                "editor_sample": self.first_row.get(header, f"{header} sample"),
            })
            for header in self.headers
        )

    def load_data(self):
        format = self.file.name.split(".")[-1]
        with self.file.open() as f:
            if format == 'csv':
                f = TextIOWrapper(f, "utf-8")
            return Dataset().load(f, format=format)

    def populate_data(self):
        data = self.load_data()
        if not data.height:
            raise Exception("Empty file")

        self.headers = data.headers
        self.first_row = data.dict[0]
        self.save()

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Row(object):

    qrcode = ""
