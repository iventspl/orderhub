from django import forms
from django.contrib.auth import get_user_model
from users.models import UserProfile, Membership
from warehouse.models import Warehouse

User = get_user_model()

class StaffAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.company_id = kwargs.pop('company_id', None)
        super().__init__(*args, **kwargs)
        if self.company_id:
            self.fields['assigned_warehouse'].queryset = Warehouse.objects.filter(company_id=self.company_id)
        else:
            self.fields['assigned_warehouse'].queryset = Warehouse.objects.none()

    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=True)

    class Meta:
        model = UserProfile
        fields = ['email', 'phone_number', 'address', 'city', 'state', 'zip_code', 'country', 'assigned_warehouse','active_company', 'assigned_role', 'department']
        widgets ={
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'assigned_warehouse': forms.Select(attrs={'class': 'form-control'}),
            # 'active_company': forms.Select(attrs={'class': 'form-control'}),
            'assigned_role': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'email': 'Email',
            'phone_number': 'Phone Number',
            'address': 'Address',
            'city': 'City',
            'state': 'State',
            'zip_code': 'Zip Code',
            'country': 'Country',
            'assigned_warehouse': 'Assigned Warehouse',
            # 'active_company': 'Active Company',
            'assigned_role': 'Assigned Role',
            'department': 'Department',
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists.')
        return username

    def save(self, commit=True):
        user_profile = super().save(commit=False)
        user = getattr(user_profile, 'user', None)

        if user is None:
            user = User()

        user.username = self.cleaned_data['username']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.set_password(self.cleaned_data['password'])

        if self.company_id:
            user_profile.active_company_id = self.company_id

        if commit:
            user.save()
            user_profile.user = user
            user_profile.save()

            if user_profile.active_company_id and user_profile.assigned_role:
                Membership.objects.update_or_create(
                    user=user,
                    company_id=user_profile.active_company_id,
                    defaults={'role': user_profile.assigned_role},
                )
        else:
            user_profile.user = user

        return user_profile