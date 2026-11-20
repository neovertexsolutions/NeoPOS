from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.utils import timezone
from datetime import datetime, timedelta
from sales.models import Sale, SaleItem
from purchases.models import Purchase
from expenses.models import Expense
from products.models import Product

@login_required
def reports_dashboard(request):
    period = request.GET.get('period', 'month')
    now = timezone.now()
    today = now.date()

    if period == 'today':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today
    elif period == 'custom':
        start_str = request.GET.get('start_date')
        end_str = request.GET.get('end_date')
        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date() if start_str else (today - timedelta(days=30))
        except (ValueError, TypeError):
            start_date = today - timedelta(days=30)
        try:
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date() if end_str else today
        except (ValueError, TypeError):
            end_date = today
    else: # month default
        start_date = today.replace(day=1)
        end_date = today

    # Sales in range
    sales_qs = Sale.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
    total_sales_revenue = sales_qs.aggregate(Sum('total'))['total__sum'] or 0
    total_sales_count = sales_qs.count()

    # Purchases in range
    purchases_qs = Purchase.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
    total_purchases = purchases_qs.aggregate(Sum('total'))['total__sum'] or 0

    # Expenses in range
    expenses_qs = Expense.objects.filter(date__gte=start_date, date__lte=end_date)
    total_expenses = expenses_qs.aggregate(Sum('amount'))['amount__sum'] or 0

    # Cost of goods sold (COGS) for items sold in this period
    sale_items = SaleItem.objects.filter(sale__created_at__date__gte=start_date, sale__created_at__date__lte=end_date)
    cogs = 0
    for item in sale_items.select_related('product'):
        prod_cost = item.product.purchase_price if item.product else 0
        cogs += (prod_cost * item.quantity)

    # Net Profit
    gross_profit = float(total_sales_revenue) - float(cogs)
    net_profit = gross_profit - float(total_expenses)

    # Top selling products
    top_products = SaleItem.objects.filter(
        sale__created_at__date__gte=start_date, 
        sale__created_at__date__lte=end_date
    ).values('product_name').annotate(
        units_sold=Sum('quantity'),
        revenue=Sum('total')
    ).order_by('-units_sold')[:8]

    # Daily breakdown for chart (last 14 days or in range)
    chart_days = 14
    daily_labels = []
    daily_sales_data = []
    daily_expense_data = []

    for i in range(chart_days - 1, -1, -1):
        day = today - timedelta(days=i)
        daily_labels.append(day.strftime('%b %d'))
        
        day_sales = Sale.objects.filter(created_at__date=day).aggregate(Sum('total'))['total__sum'] or 0
        day_expenses = Expense.objects.filter(date=day).aggregate(Sum('amount'))['amount__sum'] or 0
        
        daily_sales_data.append(float(day_sales))
        daily_expense_data.append(float(day_expenses))

    # Payment method breakdown
    payment_methods = sales_qs.values('payment_method').annotate(
        count=Count('id'),
        amount=Sum('total')
    )

    return render(request, 'reports/reports.html', {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales_revenue': total_sales_revenue,
        'total_sales_count': total_sales_count,
        'total_purchases': total_purchases,
        'total_expenses': total_expenses,
        'cogs': cogs,
        'gross_profit': gross_profit,
        'net_profit': net_profit,
        'top_products': top_products,
        'payment_methods': payment_methods,
        'daily_labels': daily_labels,
        'daily_sales_data': daily_sales_data,
        'daily_expense_data': daily_expense_data,
    })
