from django.urls import path
from . import views
app_name = 'discussion'

urlpatterns = [
    path('', views.discussion_dashboard, name='discussion_dashboard'),
]
