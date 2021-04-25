from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.contrib.auth.models import Group, Permission
from django.shortcuts import redirect, render, reverse
from django.views import generic

from apps.account.models import USER_PERMISSIONS
from apps.common.views import PAGINATE_BY


class GroupAccountView(LoginRequiredMixin):

    def get_queryset(self):
        user = self.request.user
        return super().get_queryset().filter(name__startswith=f'{user.account.id}|').all()


class CustomPermissionField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, perm):
        return perm.name


class GroupForm(forms.ModelForm):

    permissions = CustomPermissionField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # List all perms
        self.fields['permissions'].queryset = Permission.objects.filter(codename__in=USER_PERMISSIONS)

    class Meta:
        model = Group
        fields = ('name', 'permissions')


class IndexView(PermissionRequiredMixin, GroupAccountView, generic.ListView):
    model = Group
    context_object_name = 'groups'
    template_name = 'group/index.html'
    permission_required = 'auth.view_group'
    paginate_by = PAGINATE_BY


class CreateView(PermissionRequiredMixin, generic.CreateView):
    context_object_name = 'groups'
    template_name = 'group/new.html'
    permission_required = ('auth.view_group', 'auth.add_group')

    def get(self, *args, **kwargs):
        form = GroupForm()
        return render(self.request, self.template_name, {'form': form})

    def post(self, *args, **kwargs):
        account_id = self.request.user.account.id
        form = GroupForm(self.request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.name = f"{account_id}|{instance.name}"
            instance.save()
            form.save_m2m()

            messages.add_message(self.request, messages.INFO, 'Create team success!')
            return redirect(reverse("account:group_index"))

        return render(self.request, self.template_name, {'form': form})


class DetailView(PermissionRequiredMixin, GroupAccountView, generic.DetailView):
    model = Group
    template_name = 'group/detail.html'
    permission_required = ('auth.view_group', 'auth.change_group')

    def get(self, *args, **kwargs):
        group = self.get_object()
        form = GroupForm(instance=group)
        return render(self.request, self.template_name, {'form': form, 'group': group})

    def post(self, *args, **kwargs):
        account_id = self.request.user.account.id
        group = self.get_object()
        form = GroupForm(self.request.POST, instance=group)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.name = f"{account_id}|{instance.name}"
            instance.save()
            form.save_m2m()

            messages.add_message(self.request, messages.INFO, 'Save success!')
            return redirect(reverse("account:group_detail", kwargs=kwargs))

        return render(self.request, self.template_name, {'form': form, 'group': group})
