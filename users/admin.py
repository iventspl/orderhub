from django.contrib import admin

from .models import User, UserProfile, Company, Membership, Department
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    ordering = ('-date_joined',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'phone_number', 'city', 'country')
    search_fields = ('user__username', 'email', 'phone_number', 'city', 'country')
    list_filter = ('city', 'country')
    ordering = ('user__username',)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'city', 'zip_code', 'country')
    search_fields = ('name', 'address', 'city', 'zip_code', 'country')
    list_filter = ('city', 'country')
    ordering = ('name',)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'role')
    search_fields = ('user__username', 'company__name', 'role')
    list_filter = ('role',)
    ordering = ('user__username',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('department', 'user', 'company')
    search_fields = ('department', 'user__username', 'company__name')
    list_filter = ('department',)
    ordering = ('department',)