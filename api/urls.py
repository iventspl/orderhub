from django.urls import path
from . import views


app_name = 'api' 

urlpatterns = [
    path('sales-orders/', views.api_get_sales_orders, name='api_get_sales_orders'),
    path('products/search/', views.api_search_products, name='api_search_products'),
]
