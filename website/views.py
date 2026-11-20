from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from sales.models import Sale
from products.models import Product
from customers.models import Customer
from purchases.models import Purchase
from accounts.models import UpgradeRequest

def home_landing(request):
    """Marketing Landing Page (Section 15)"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'website/index.html')


def about_page(request):
    """About page"""
    return render(request, 'website/about.html')


def pricing_page(request):
    """Pricing page"""
    return render(request, 'website/pricing.html')


def contact_page(request):
    """Contact page"""
    return render(request, 'website/contact.html')


def pos_showcase_page(request):
    """POS showcase page"""
    return render(request, 'website/pos_showcase.html')


@login_required
def dashboard_view(request):
    """Main System Dashboard (Section 3)"""
    today = timezone.now().date()

    # 1. Today's Sales & Orders
    today_sales_qs = Sale.objects.filter(created_at__date=today, cashier=request.user)
    today_sales_total = today_sales_qs.aggregate(Sum('total'))['total__sum'] or 0
    today_orders_count = today_sales_qs.count()

    # 2. Total Products
    total_products_count = Product.objects.filter(is_active=True, created_by=request.user).count()

    # 3. Total Customers
    total_customers_count = Customer.objects.filter(created_by=request.user).count()

    # 4. Low Stock
    all_products = Product.objects.filter(is_active=True, created_by=request.user).select_related('category')
    low_stock_products = [p for p in all_products if p.stock <= p.minimum_stock]
    low_stock_count = len(low_stock_products)

    # 5. Recent Sales (last 8)
    recent_sales = Sale.objects.filter(cashier=request.user).select_related('customer', 'cashier').order_by('-created_at')[:8]

    # 6. Sales Chart data (Last 7 Days)
    chart_labels = []
    chart_sales = []
    chart_orders = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        chart_labels.append(day.strftime('%a (%b %d)'))
        day_qs = Sale.objects.filter(created_at__date=day, cashier=request.user)
        chart_sales.append(float(day_qs.aggregate(Sum('total'))['total__sum'] or 0))
        chart_orders.append(day_qs.count())

    return render(request, 'dashboard.html', {
        'today_sales_total': today_sales_total,
        'today_orders_count': today_orders_count,
        'total_products_count': total_products_count,
        'low_stock_count': low_stock_count,
        'total_customers_count': total_customers_count,
        'recent_sales': recent_sales,
        'low_stock_products': low_stock_products[:8],
        'chart_labels': chart_labels,
        'chart_sales': chart_sales,
        'chart_orders': chart_orders,
        'latest_upgrade_request': request.user.upgrade_requests.first(),
    })

def privacy_policy(request):
    """Privacy Policy Page"""
    return render(request, 'website/privacy.html')

def terms_of_service(request):
    """Terms of Service Page"""
    return render(request, 'website/terms.html')

def security(request):
    """Security Architecture & Data Protection Page"""
    return render(request, 'website/security.html')

def hardware_support(request):
    """Hardware Compatibility & Setup Guide Page"""
    return render(request, 'website/hardware.html')
