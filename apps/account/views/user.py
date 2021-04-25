from captcha.fields import CaptchaField
from django import forms
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.contrib.auth.models import Group, Permission
from django.shortcuts import redirect, render, reverse
from django.views import generic

from apps.account.models import USER_PERMISSIONS, Account, User
from apps.common.views import PAGINATE_BY, AccountView
from apps.page.templatetags.group_name import group_name


class CustomGroupField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, group):
        return group_name(group)


class UserForm(forms.ModelForm):

    groups = CustomGroupField(
        required=False,
        queryset=None,
        widget=forms.CheckboxSelectMultiple
    )

    password = forms.CharField(required=False)
    account = forms.ModelChoiceField(required=False, queryset=None)

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        account = request.user.account

        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['groups'].queryset = Group.objects.filter(name__startswith=f"{account.id}|")

    class Meta:
        model = User
        fields = ('username', 'role', 'is_active', 'groups')


class IndexView(PermissionRequiredMixin, AccountView, generic.ListView):
    model = User
    context_object_name = 'users'
    template_name = 'user/index.html'
    paginate_by = PAGINATE_BY
    permission_required = 'account.view_user'


class CreateView(PermissionRequiredMixin, generic.CreateView):
    model = User
    template_name = 'user/new.html'
    permission_required = 'account.add_user'

    def get(self, *args, **kwargs):
        form = UserForm(request=self.request)
        return render(self.request, self.template_name, {'form': form})

    def post(self, *args, **kwargs):
        account = self.request.user.account
        form = UserForm(self.request.POST, request=self.request)

        if form.is_valid():
            instance = form.save(commit=False)
            if not instance.account_id:
                instance.account = account
            if form.cleaned_data['password']:
                instance.set_password(form.cleaned_data['password'])
            instance.save()
            form.save_m2m()

            messages.add_message(self.request, messages.INFO, 'Create user success!')
            return redirect(reverse("account:user_detail", kwargs={"pk": instance.id}))

        return render(self.request, self.template_name, {'form': form})


class DetailView(AccountView, generic.DetailView):
    model = User
    template_name = 'user/detail.html'
    permission_required = ('account.view_user', 'account.change_user')

    def get(self, *args, **kwargs):
        user = self.get_object()
        form = UserForm(instance=user, request=self.request)

        return render(self.request, self.template_name, {'form': form, 'user': user})

    def post(self, *args, **kwargs):
        user = self.get_object()
        account = self.request.user.account
        form = UserForm(self.request.POST, instance=user, request=self.request)

        if form.is_valid():
            instance = form.save(commit=False)
            if not instance.account_id:
                instance.account = account

            # Add all perms for admin
            perms = Permission.objects.filter(codename__in=USER_PERMISSIONS)
            if instance.role == "admin":
                instance.user_permissions.add(*perms)
            else:
                instance.user_permissions.remove(*perms)

            if form.cleaned_data['password']:
                instance.set_password(form.cleaned_data['password'])
            instance.save()
            form.save_m2m()

            messages.add_message(self.request, messages.INFO, 'Save success!')
            return redirect(reverse("account:user_detail", kwargs=kwargs))

        return render(self.request, self.template_name, {'form': form, 'user': user})


class ProfileView(LoginRequiredMixin, generic.View):
    model = User
    template_name = 'user/profile.html'

    def get(self, *args, **kwrags):
        return render(self.request, self.template_name)


class RegisterForm(forms.ModelForm):
    captcha = CaptchaField()
    password = forms.CharField()

    class Meta:
        model = User
        fields = ('username', 'password')


class RegisterView(generic.CreateView):
    model = User
    template_name = 'user/register.html'

    def get(self, *args, **kwargs):
        form = RegisterForm()
        return render(self.request, self.template_name, {'form': form})

    def post(self, *args, **kwargs):
        form = RegisterForm(self.request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            account = Account.objects.create(name=instance.username)
            instance.account_id = account.id
            instance.role = "admin"

            instance.set_password(form.cleaned_data['password'])
            instance.save()

            # Add all perms for admin
            perms = Permission.objects.filter(codename__in=USER_PERMISSIONS)
            instance.user_permissions.add(*perms)

            login(self.request, instance)
            messages.add_message(self.request, messages.INFO, 'Register success!')
            return redirect("/")

        messages.add_message(self.request, messages.ERROR, 'Register failed!')
        return render(self.request, self.template_name, {'form': form})
