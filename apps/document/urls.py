from django.urls import path

from . import views

app_name = 'document'

urlpatterns = [
    path('<int:pk>/delete', views.DeleteView.as_view(), name='delete'),
    path('<int:pk>/download', views.DownloadView.as_view(), name='download'),
    path('<int:pk>/editor', views.EditorView.as_view(), name='editor'),
    path('<int:pk>', views.DetailView.as_view(), name='detail'),
    path('new', views.CreateView.as_view(), name='new'),
    path('', views.IndexView.as_view(), name='index'),
]
