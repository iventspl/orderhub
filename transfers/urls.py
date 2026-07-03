from django.urls import path

from . import views

app_name = 'transfers'

urlpatterns = [
    path('', views.transfers_list, name='transfers_list'),
    path('create/', views.create_transfer, name='create_transfer'),
    path('<int:transfer_id>/edit/', views.edit_transfer, name='edit_transfer'),
    path('<int:transfer_id>/delete/', views.delete_transfer, name='delete_transfer'),
    path('api/get-products/<int:warehouse_id>/', views.get_products_by_warehouse, name='get_products_by_warehouse'),
]
