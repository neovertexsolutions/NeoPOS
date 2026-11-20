from django.contrib import admin
from .models import Ticket, TicketReply

class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    extra = 1

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'subject', 'user', 'category', 'priority', 'status', 'created_at')
    list_editable = ('status', 'priority')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('ticket_number', 'subject', 'user__username', 'user__email')
    readonly_fields = ('ticket_number', 'created_at', 'updated_at')
    inlines = [TicketReplyInline]

@admin.register(TicketReply)
class TicketReplyAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'user', 'created_at')
    search_fields = ('ticket__ticket_number', 'user__username', 'message')
