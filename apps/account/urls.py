from django.urls import path

from apps.account.views import user, group, account

app_name = 'account'

urlpatterns = [
    path('users/<int:pk>', user.DetailView.as_view(), name='user_detail'),
    path('users/new', user.CreateView.as_view(), name='user_new'),
    path('users', user.IndexView.as_view(), name='user_index'),

    path('profile', user.ProfileView.as_view(), name='profile_detail'),
    path('register', user.RegisterView.as_view(), name='user_register'),
    path('detail', account.DetailView.as_view(), name='account_detail'),

    path('groups/<int:pk>', group.DetailView.as_view(), name='group_detail'),
    path('groups/new', group.CreateView.as_view(), name='group_new'),
    path('groups', group.IndexView.as_view(), name='group_index'),
]
