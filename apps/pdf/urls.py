from django.urls import path

from . import views

app_name = 'pdf'

urlpatterns = [
    path('background/<filename>.pdf', views.PdfView.as_view(), name='background'),
]
