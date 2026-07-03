from django.contrib import admin

from .models import Tracking
@admin.register(Tracking)
class TrackingAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'carrier', 'status', 'location', 'created_by', 'created_on', 'updated_on')
    search_fields = ('tracking_number', 'carrier', 'status', 'location')
    list_filter = ('status', 'updated_on')
    ordering = ('-updated_on',)