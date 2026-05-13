from django.urls import path

from . import views

app_name = 'tracking'

urlpatterns = [
    path('', views.tracking_list, name='tracking_list'),
]
