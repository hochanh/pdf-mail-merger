from django.contrib.auth.mixins import LoginRequiredMixin


PAGINATE_BY = 100


class AccountView(LoginRequiredMixin):
    def get_queryset(self):
        user = self.request.user
        return super().get_queryset().filter(account=user.account)
