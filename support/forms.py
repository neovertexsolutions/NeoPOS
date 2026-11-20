from django import forms
from .models import Ticket, TicketReply

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['subject', 'category', 'priority', 'description', 'attachment']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class TicketReplyForm(forms.ModelForm):
    class Meta:
        model = TicketReply
        fields = ['message', 'attachment']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write your reply...'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
