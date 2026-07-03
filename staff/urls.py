from django.urls import path
from . import views
app_name = 'staff'

urlpatterns = [
    path('', views.staff_dashboard, name='staff_dashboard'),
    path('api/staff-details/<int:pk>/', views.api_staff_details, name='api_staff_details'),
    # path('add/', views.staff_add, name='staff_add'),
]
