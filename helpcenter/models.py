from django.db import models

class HelpCenterTicket(models.Model):
    class TicketStatus(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    class PriorityLevel(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    class Department(models.TextChoices):
        IT = 'it', 'IT'
        HR = 'hr', 'HR'
        FINANCE = 'finance', 'Finance'
        SALES = 'sales', 'Sales'
        SUPPORT = 'support', 'Support'

    ticket_number = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(
        max_length=20,
        choices=PriorityLevel.choices,
        default=PriorityLevel.MEDIUM
    )
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.OPEN
    )
    department = models.CharField(
        max_length=20,
        choices=Department.choices,
        default=Department.SUPPORT
    )
    assigned_to = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='helpcenter_tickets')
    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='helpcenter_tickets')

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.ticket_number:
            from django.utils import timezone

            self.ticket_number = (f"TCK-{timezone.now():%Y%m%d}-{self.pk:06d}")
            super().save(update_fields=['ticket_number'])

    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.title}"


class HelpCenterTicketHistory(models.Model):
    ticket = models.ForeignKey(HelpCenterTicket, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=255)
    performed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    performed_on = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='helpcenter_ticket_history')

    def __str__(self):
        return f"History for Ticket {self.ticket.ticket_number} - Action: {self.action}"


class HelpCenterTicketReply(models.Model):
    ticket = models.ForeignKey(HelpCenterTicket, on_delete=models.CASCADE, related_name='replies')
    comment = models.CharField(max_length=255)
    commented_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    commented_on = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='helpcenter_ticket_replies')

    def __str__(self):
        return f"Reply on Ticket {self.ticket.ticket_number} by {self.commented_by}"
