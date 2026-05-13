from django.urls import path

from . import views

app_name = 'transfers'

urlpatterns = [
    path('', views.transfers_list, name='transfers_list'),
]
