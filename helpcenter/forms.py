from django import forms
from .models import HelpCenterTicket, HelpCenterTicketReply


class HelpTicketForm(forms.ModelForm):
    class Meta: 
        model = HelpCenterTicket
        fields = ['title', 'description', 'priority', 'department']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Short title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe the issue...'}),
            'priority': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Select priority'}),
            'department': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Select department'}),
        }



class HelpTicketReplyForm(forms.ModelForm):
    class Meta:
        model = HelpCenterTicketReply
        fields = ['comment']
        widgets = {
            'comment': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add a reply...'}),
        }