from django.contrib import admin
from .models import Logger
# Register your models here.

@admin.register(Logger)
class LoggerAdmin(admin.ModelAdmin):
    list_display = ('action', 'timestamp', 'user', 'details', 'content_type', 'object_id')
    list_filter = ('timestamp', 'user', 'content_type')
    search_fields = ('action', 'details', 'user__username', 'user__email')
    readonly_fields = ('timestamp',)