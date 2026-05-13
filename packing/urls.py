from django.urls import path

from . import views

app_name = 'packing'

urlpatterns = [
    path('', views.packing_list, name='packing_list'),
]
