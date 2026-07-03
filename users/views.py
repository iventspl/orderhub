from django.contrib.auth import authenticate, login, logout, get_user_model
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from .forms import LoginForm


def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('mainapp:home')
            else:
                form.add_error(None, "Invalid username or password")
    context = {
        'form': form,
    }
    return render(request, 'users/authentication/login.html', context)


@require_POST
def logout_view(request):
    
    logout(request)
    return redirect('mainapp:home')


# disabled, only company admins can create users
# def register_view(request):
#     form = RegisterForm(request.POST or None)
#     if request.method == 'POST':
#         if form.is_valid():
#             username = form.cleaned_data['username']
#             password = form.cleaned_data['password']
#             user_model = get_user_model()
#             user = user_model.objects.create(username=username, is_active=True)
#             user.set_password(password)
#             user.save()
#             login(request, user)
#             return redirect('mainapp:home')
#     context = {
#         'form': form,
#     }
#     return render(request, 'users/authentication/register.html', context)