from django.urls import path

from . import views

app_name = 'warehouse'

urlpatterns = [
    path('', views.warehouse_list, name='warehouse_list'),
]
