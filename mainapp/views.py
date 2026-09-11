from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def home_view(request):
    # All required variables are passed to template via context_processors.py
    context = {
        'page': 'home',
    }
    return render(request, 'mainapp/home.html', context)