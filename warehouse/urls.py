from django.urls import path

from . import views

app_name = 'warehouse'

urlpatterns = [
    path('', views.warehouse_list, name='warehouse_list'),
    path('type/<str:warehouse_type>/', views.warehouse_list, name='warehouse_list_by_type'),
    path('create/', views.create_warehouse, name='create'),
    path('types/', views.get_warehouse_types, name='get_warehouse_types'),
    path('<int:warehouse_id>/edit/', views.edit_warehouse, name='edit_warehouse'),
    path(
        '<int:warehouse_id>/product/<int:product_id>/delete/',
        views.delete_warehouse_product,
        name='delete_warehouse_product',
    ),
]
