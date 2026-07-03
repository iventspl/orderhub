from django.urls import path
from . import views
app_name = 'helpcenter'

urlpatterns = [
    path('', views.help_center_dashboard, name='help_center_dashboard'),
    path('submit_ticket/', views.submit_ticket, name='submit_ticket'),
    path('submit_ticket_reply/<int:ticket_id>/', views.submit_ticket_reply, name='submit_ticket_reply'),
    path('api/update-ticket-status/<int:ticket_id>/', views.update_ticket_status, name='update_ticket_status'),
    path('api/update-ticket-assignee/ticket/<int:ticket_id>/assignee/<int:assignee_id>/', views.update_ticket_assignee, name='update_ticket_assignee'),
]
