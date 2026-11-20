from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Ticket, TicketReply
from .forms import TicketForm, TicketReplyForm

@login_required
def support_ticket_list(request):
    tickets = Ticket.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'support/ticket_list.html', {'tickets': tickets})

@login_required
def support_ticket_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            messages.success(request, 'Your support ticket has been submitted successfully.')
            return redirect('support_ticket_list')
    else:
        form = TicketForm()
    return render(request, 'support/ticket_form.html', {'form': form})

@login_required
def support_ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    replies = ticket.replies.all().order_by('created_at')
    
    if request.method == 'POST':
        form = TicketReplyForm(request.POST, request.FILES)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.ticket = ticket
            reply.user = request.user
            reply.save()
            
            # Optional: update ticket status to pending if user replies
            if ticket.status == 'Resolved':
                ticket.status = 'Open'
                ticket.save()
                
            messages.success(request, 'Reply added successfully.')
            return redirect('support_ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketReplyForm()
        
    return render(request, 'support/ticket_detail.html', {
        'ticket': ticket,
        'replies': replies,
        'form': form
    })
