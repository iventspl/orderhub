from django.contrib.auth import authenticate, login
from django.shortcuts import render
from django.http import HttpResponse

def login_view(request):
    return render(request, 'users/authentication/login.html')