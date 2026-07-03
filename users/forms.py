from django import forms
from django.contrib.auth import get_user_model


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'})) 

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            User = get_user_model()
            try:
                user = User.objects.get(username=username)
                if not user.check_password(password):
                    raise forms.ValidationError("Invalid username or password")
            except User.DoesNotExist:
                raise forms.ValidationError("Invalid username or password")

        return cleaned_data
    


# disabled, only company admins can create users
# class RegisterForm(forms.Form):
#     username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
#     password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
#     confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

#     def clean(self):
#         cleaned_data = super().clean()
#         password = cleaned_data.get('password')
#         username = cleaned_data.get('username')
#         confirm_password = cleaned_data.get('confirm_password')

#         if password and confirm_password and password != confirm_password:
#             raise forms.ValidationError("Passwords do not match")
        
#         if username:
#             User = get_user_model()
#             if User.objects.filter(username=username).exists():
#                 raise forms.ValidationError("Username already exists")

#         return cleaned_data