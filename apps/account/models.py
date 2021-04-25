from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimestampModel

USER_PERMISSIONS = [
    # Account
    'add_account',
    'change_account',
    'delete_account',
    'view_account',

    # User
    'add_user',
    'change_user',
    'delete_user',
    'view_user',

    # Group
    'add_group',
    'change_group',
    'delete_group',
    'view_group',

    # Document
    'add_document',
    'change_document',
    'delete_document',
    'view_document',
]


def trial_time():
    return timezone.now() + timedelta(days=30)


class Account(TimestampModel, models.Model):
    name = models.CharField(_("Name"), blank=False, null=False, max_length=255, db_index=True)
    plan = models.CharField(choices=(("trial", "Trial"), ("pro", "Pro")),
                            max_length=255, default="trial")
    plan_end_at = models.DateTimeField(default=trial_time)
    plan_limit = models.PositiveIntegerField(default=10)

    def __str__(self):
        return self.name


class User(AbstractUser):
    account = models.ForeignKey(Account, on_delete=models.PROTECT, null=False)
    role = models.CharField(_("Role"),
                            choices=(('admin', "Admin"), ('member', "Member")),
                            null=False,
                            max_length=255,
                            default="member")
    name = models.CharField(_("Name"), blank=True, null=False, max_length=255)
    first_name = None
    last_name = None
