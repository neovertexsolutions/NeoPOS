from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import Expense, ExpenseCategory
from django.utils import timezone
from datetime import datetime

@login_required
def expenses_list(request):
    categories = ExpenseCategory.objects.all()
    expenses = Expense.objects.select_related('category', 'created_by').order_by('-date', '-created_at')

    category_id = request.GET.get('category')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if category_id:
        expenses = expenses.filter(category_id=category_id)
    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)

    total_amount = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    if request.method == 'POST':
        cat_id = request.POST.get('category_id')
        amount = request.POST.get('amount')
        description = request.POST.get('description', '')
        date_str = request.POST.get('date') or timezone.now().strftime('%Y-%m-%d')
        
        category = get_object_or_404(ExpenseCategory, pk=cat_id)
        Expense.objects.create(
            category=category,
            amount=amount,
            description=description,
            date=date_str,
            created_by=request.user
        )
        messages.success(request, f"Expense of Rs. {amount} recorded.")
        return redirect('expenses_list')

    return render(request, 'expenses/expenses.html', {
        'expenses': expenses,
        'categories': categories,
        'total_amount': total_amount,
        'selected_category': category_id,
        'start_date': start_date,
        'end_date': end_date
    })

@login_required
def expense_categories(request):
    categories = ExpenseCategory.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name and not ExpenseCategory.objects.filter(name__iexact=name).exists():
            ExpenseCategory.objects.create(name=name, description=description)
            messages.success(request, f"Category '{name}' added.")
        else:
            messages.error(request, "Category already exists or invalid.")
        return redirect('expense_categories')

    return render(request, 'expenses/categories.html', {'categories': categories})

@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, "Expense record deleted.")
    return redirect('expenses_list')
