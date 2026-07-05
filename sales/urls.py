from django.urls import path

from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sales_list, name="sales_list"),
    path('edit/', views.edit_sales_order, name="edit_sales_order"),
    path('delete/<int:order_id>/', views.delete_sales_order, name="delete_sales_order"),
    path('transition/<int:order_id>/', views.transition_order, name="transition_order"),
    # path('create/', views.create_order, name="create_order"),
    # path('rows-api', views.sales_list_rows_api, name="sales_list_rows"),
]
