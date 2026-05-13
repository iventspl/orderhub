# ============================================================
#  DJANGO – ŚCIĄGA  (tylko przykłady, resztę robisz sam)
# ============================================================


# ════════════════════════════════════════════════════════════
#  1. URLs  (urls.py)
# ════════════════════════════════════════════════════════════

from django.urls import path, include
from . import views

app_name = 'mainapp'          # namespace – używasz go w szablonach jako mainapp:home

urlpatterns = [
    path('',               views.HomeView.as_view(),       name='home'),
    path('about/',         views.AboutView.as_view(),      name='about'),
    path('contact/',       views.ContactView.as_view(),    name='contact'),

    # URL z parametrem (np. /post/42/)
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),

    # Dołączanie innej aplikacji
    path('accounts/',      include('users.urls', namespace='users')),
]


# ════════════════════════════════════════════════════════════
#  2. VIEWS  (views.py)
# ════════════════════════════════════════════════════════════

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

# --- Najprostszy widok (class-based) ---
class HomeView(TemplateView):
    template_name = 'mainapp/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Strona główna'   # dostępne w szablonie jako {{ title }}
        return ctx


# --- Widok z logiką GET i POST ---
class ContactView(View):
    def get(self, request):
        return render(request, 'mainapp/contact.html')

    def post(self, request):
        # przetwórz dane formularza...
        return redirect('mainapp:home')


# --- Widok wymagający zalogowania ---
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'mainapp/dashboard.html'
    login_url = '/accounts/login/'


# --- Widok z parametrem z URL ---
class PostDetailView(View):
    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        return render(request, 'mainapp/post_detail.html', {'post': post})


# ════════════════════════════════════════════════════════════
#  3. TEMPLATES  (templates/mainapp/)
# ════════════════════════════════════════════════════════════

# --- base.html (szkielet, raz, dziedziczą po nim wszystkie) ---

"""
{% load static %}
<!DOCTYPE html>
<html lang="pl">
<head>
    <title>{% block title %}Strona{% endblock %}</title>
    <link rel="stylesheet" href="{% static 'css/base.css' %}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav>
        <a href="{% url 'mainapp:home' %}">Home</a>
        <a href="{% url 'mainapp:about' %}">About</a>
        {% if user.is_authenticated %}
            <a href="{% url 'users:logout' %}">Wyloguj</a>
        {% else %}
            <a href="{% url 'users:login' %}">Zaloguj</a>
        {% endif %}
    </nav>

    <main>
        {% block content %}{% endblock %}
    </main>

    <script src="{% static 'js/base.js' %}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
"""


# --- home.html (każda podstrona wygląda tak samo) ---

"""
{% extends 'mainapp/base.html' %}
{% load static %}

{% block title %}Home{% endblock %}

{% block extra_css %}
    <link rel="stylesheet" href="{% static 'css/home.css' %}">
{% endblock %}

{% block content %}
    <h1>{{ title }}</h1>
    <p>Treść strony głównej.</p>

    {% for item in items %}
        <p>{{ item.name }}</p>
    {% empty %}
        <p>Brak elementów.</p>
    {% endfor %}
{% endblock %}
"""


# --- Formularz w szablonie ---

"""
{% block content %}
<form method="POST" enctype="multipart/form-data">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Wyślij</button>
</form>
{% endblock %}
"""

# enctype="multipart/form-data"  ← wymagane tylko gdy przesyłasz pliki/obrazy


# ════════════════════════════════════════════════════════════
#  4. STATIC FILES
# ════════════════════════════════════════════════════════════

# Struktura folderów:
#   mainapp/
#     static/
#       css/
#         base.css
#         home.css        ← osobny plik dla danej strony
#       js/
#         base.js
#       img/
#         logo.png

# W szablonie zawsze:
#   {% load static %}                       ← na początku pliku
#   {% static 'css/base.css' %}             ← ścieżka względem static/
#   {% static 'img/logo.png' %}

# settings.py (już skonfigurowane):
#   STATIC_URL  = 'static/'
#   STATIC_ROOT = BASE_DIR / 'staticfiles'  ← używane tylko na produkcji
#   MEDIA_URL   = 'media/'
#   MEDIA_ROOT  = BASE_DIR / 'media'        ← przesłane pliki użytkowników


# ════════════════════════════════════════════════════════════
#  5. MODELS  (models.py)
# ════════════════════════════════════════════════════════════

from django.db import models
from django.conf import settings

class Post(models.Model):
    author  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title   = models.CharField(max_length=200)
    body    = models.TextField()
    image   = models.ImageField(upload_to='posts/', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# Po każdej zmianie modelu:
#   python manage.py makemigrations
#   python manage.py migrate


# ════════════════════════════════════════════════════════════
#  6. FORMS  (forms.py)
# ════════════════════════════════════════════════════════════

from django import forms
# from .models import Post

# --- Formularz niezwiązany z modelem ---
class ContactForm(forms.Form):
    name    = forms.CharField(max_length=100)
    email   = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)


# --- Formularz oparty na modelu ---
class PostForm(forms.ModelForm):
    class Meta:
        model  = Post
        fields = ['title', 'body', 'image']


# --- Obsługa formularza w widoku ---
class PostCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = PostForm()
        return render(request, 'mainapp/post_form.html', {'form': form})

    def post(self, request):
        form = PostForm(request.POST, request.FILES)   # request.FILES dla obrazów
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('mainapp:home')
        return render(request, 'mainapp/post_form.html', {'form': form})


# ════════════════════════════════════════════════════════════
#  7. AUTENTYKACJA  (users/urls.py + views.py)
# ════════════════════════════════════════════════════════════

from django.contrib.auth import views as auth_views

# urls.py
urlpatterns_auth_example = [
    path('login/',    auth_views.LoginView.as_view(template_name='users/authentication/login.html'),   name='login'),
    path('logout/',   auth_views.LogoutView.as_view(next_page='/'),  name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
]

# settings.py – dokąd przekierować po zalogowaniu/wylogowaniu:
#   LOGIN_REDIRECT_URL  = '/'
#   LOGOUT_REDIRECT_URL = '/'
#   LOGIN_URL           = '/accounts/login/'


# ════════════════════════════════════════════════════════════
#  KOLEJNOŚĆ PRACY (każda nowa strona)
# ════════════════════════════════════════════════════════════

# 1. models.py   → dodaj model jeśli potrzebny → makemigrations + migrate
# 2. urls.py     → dodaj path(...)
# 3. views.py    → dodaj klasę/funkcję widoku
# 4. template    → stwórz plik HTML dziedziczący z base.html
# 5. static      → dodaj CSS/JS jeśli potrzebne
# 6. runserver   → sprawdź w przeglądarce
