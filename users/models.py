from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class Company(models.Model):
    company_code = models.CharField(max_length=15, unique=True, blank=True, null=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.company_code:
            self.company_code = self.generate_company_code()
        super().save(*args, **kwargs)

    def generate_company_code(self):
        import uuid
        return str(uuid.uuid4())[:15].upper()



class Membership(models.Model):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        MANAGER = 'MANAGER', 'Manager'
        EMPLOYEE = 'EMPLOYEE', 'Employee'
        ASSIGNEE = 'ASSIGNEE', 'Assignee'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=Roles.choices)  # Optional role field

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'company'], name='unique_membership_user_company')
        ]
        indexes = [
            models.Index(fields=['user'], name='membership_user_idx'),
            models.Index(fields=['company'], name='membership_company_idx'),
            models.Index(fields=['role'], name='membership_role_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.company.name} ({self.role})"



class User(AbstractUser):
    pass


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    email = models.EmailField(unique=True, max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    assigned_warehouse = models.ForeignKey('warehouse.Warehouse', on_delete=models.SET_NULL, blank=True, null=True)
    assigned_role = models.CharField(max_length=50, choices=Membership.Roles.choices, blank=True, null=True)
    active_company = models.ForeignKey(Company, on_delete=models.SET_NULL, blank=True, null=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, blank=True, null=True)

    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()
    
    def get_department_display(self):
        if self.department:
            return self.department.get_department_display()
        return None
    
    def get_role_display(self):
        if self.assigned_role:
            return Membership.Roles(self.assigned_role).label
        return None
    
    def get_initials(self):
        first_initial = self.user.first_name[0] if self.user.first_name else ''
        last_initial = self.user.last_name[0] if self.user.last_name else ''
        return f"{first_initial}{last_initial}".upper()

    def __str__(self):
        return self.user.username
    


class Department(models.Model):
    class DepartmentChoices(models.TextChoices):
        SALES = 'SALES', 'Sales'
        WAREHOUSE = 'WAREHOUSE', 'Warehouse'
        PACKING = 'PACKING', 'Packing'
        IT = 'IT', 'IT'
        HR = 'HR', 'HR'
        FINANCE = 'FINANCE', 'Finance'

    department = models.CharField(max_length=20, choices=DepartmentChoices.choices)
    user = models.ForeignKey('UserProfile', on_delete=models.CASCADE, related_name='departments')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments')

    class Meta:
        unique_together = ('department', 'company')

    def __str__(self):
        return f"{self.get_department_display()} ({self.company.name})"
