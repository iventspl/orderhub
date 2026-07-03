from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='user-login'),
    # disabled registration, only admin can create users
    # path('register/', views.register_view, name='user-register'),
    path('logout/', views.logout_view, name='user-logout'),
]
