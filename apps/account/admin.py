from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.account.models import User, Account

from django.utils.translation import gettext_lazy as _
from django import forms

from django.contrib.auth.forms import UserChangeForm, UserCreationForm


class MyUserChangeForm(UserChangeForm):
    account = forms.ModelChoiceField(queryset=Account.objects.all())


class MyUserCreationForm(UserCreationForm):
    account = forms.ModelChoiceField(queryset=Account.objects.all())

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ("account",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password', 'account', 'role')}),
        (_('Personal info'), {'fields': ('name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('account', 'username', 'password1', 'password2'),
        }),
    )
    list_display = ('id', 'username', 'email', 'name', 'is_staff', 'account', 'role')
    search_fields = ('username', 'name', 'email')

    form = MyUserChangeForm
    add_form = MyUserCreationForm


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    list_display_links = ["name"]
