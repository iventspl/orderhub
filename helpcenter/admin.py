from django.contrib import admin
from .models import HelpCenterTicket, HelpCenterTicketHistory, HelpCenterTicketReply

@admin.register(HelpCenterTicket)
class HelpCenterTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'priority', 'department', 'assigned_to', 'created_by', 'created_on')
    list_filter = ('status', 'priority', 'department')
    search_fields = ('title', 'description', 'created_by__username', 'assigned_to__username')
    ordering = ('-created_on',)


@admin.register(HelpCenterTicketReply)
class HelpCenterTicketReplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'comment', 'commented_by', 'commented_on')
    list_filter = ('commented_on',)
    search_fields = ('ticket__title', 'commented_by__username')
    ordering = ('-commented_on',)

@admin.register(HelpCenterTicketHistory)
class HelpCenterTicketHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'action', 'performed_by', 'performed_on')
    list_filter = ('performed_on',)
    search_fields = ('ticket__title', 'performed_by__username')
    ordering = ('-performed_on',)