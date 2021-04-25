from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.shortcuts import redirect, render, reverse
from django.views import generic
from apps.account.models import Account


class AccountForm(forms.ModelForm):

    class Meta:
        model = Account
        fields = ('name',)


class DetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.View):
    template_name = 'account/edit.html'
    permission_required = ('account.view_account', 'account.change_account')

    def get(self, *args, **kwargs):
        account = self.request.user.account
        form = AccountForm(instance=account)

        return render(self.request, self.template_name, {'form': form})

    def post(self, *args, **kwargs):
        account = self.request.user.account
        form = AccountForm(self.request.POST, instance=account)

        if form.is_valid():
            form.save()
            messages.add_message(self.request, messages.INFO, 'Save success!')
            return redirect(reverse("account:account_detail"))

        messages.add_message(self.request, messages.ERROR, 'Save failed!')
        return render(self.request, self.template_name, {'form': form})
