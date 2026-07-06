from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customers_list, name='customers_list'),
    path('<int:customer_id>/edit/', views.edit_customer, name='edit_customer'),
]
