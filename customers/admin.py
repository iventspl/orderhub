from django.contrib import admin

from .models import Customer
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone_number', 'created_by', 'created_on')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('created_on',)
    ordering = ('-created_on',)
