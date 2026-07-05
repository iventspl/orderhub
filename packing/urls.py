from django.urls import path

from . import views

app_name = 'packing'

urlpatterns = [
    path('', views.packing_list, name='packing_list'),
    # Batch: zmienia zaznaczone zlecenia PENDING → IN_PROGRESS
    path('start/', views.start_packing, name='start_packing'),
    path('<int:packing_order_id>/complete/', views.complete_packing, name='complete_packing'),
    path('<int:packing_order_id>/complete-partial/', views.complete_partial, name='complete_partial'),
    path('<int:packing_order_id>/ship/', views.ship_packing, name='ship_packing'),
    path('<int:packing_order_id>/deliver/', views.deliver_packing, name='deliver_packing'),
    path('<int:packing_order_id>/pdf/', views.packing_list_pdf, name='packing_list_pdf'),
    path('<int:packing_order_id>/cancel/', views.packing_started_cancel, name='packing_started_cancel'),
]
