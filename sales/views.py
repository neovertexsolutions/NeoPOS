from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Sale, SaleItem
from products.models import Product, Category
from customers.models import Customer
from inventory.models import StockMovement
from decimal import Decimal
import json

@login_required
@ensure_csrf_cookie
def pos_terminal(request):
    categories = Category.objects.all().order_by('name')
    products = Product.objects.filter(is_active=True, created_by=request.user).select_related('category').order_by('name')
    customers = Customer.objects.filter(created_by=request.user).order_by('name')
    return render(request, 'pos/pos.html', {
        'categories': categories,
        'products': products,
        'customers': customers,
    })

@login_required
def api_process_sale(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    try:
        data = json.loads(request.body)
        items_data = data.get('items', [])
        customer_id = data.get('customer_id')
        payment_method = data.get('payment_method', 'cash')
        subtotal = Decimal(str(data.get('subtotal', 0)))
        discount = Decimal(str(data.get('discount', 0)))
        tax = Decimal(str(data.get('tax', 0)))
        total = Decimal(str(data.get('total', 0)))
        amount_tendered = Decimal(str(data.get('amount_tendered', total)))
        change_amount = Decimal(str(data.get('change_amount', 0)))
        notes = data.get('notes', '')

        if not items_data:
            return JsonResponse({'success': False, 'error': 'Cart is empty. Please select products.'}, status=400)

        with transaction.atomic():
            # Validate inventory stock availability first
            for item in items_data:
                p_id = item.get('product_id')
                qty = int(item.get('quantity', 1))
                product = Product.objects.select_for_update().get(id=p_id)
                if product.stock < qty:
                    return JsonResponse({
                        'success': False, 
                        'error': f"Insufficient stock for '{product.name}'. Available: {product.stock}, Requested: {qty}"
                    }, status=400)

            customer = Customer.objects.filter(id=customer_id).first() if customer_id else None
            invoice_no = Sale.generate_invoice_number()

            # Create Sale Record
            sale = Sale.objects.create(
                invoice_number=invoice_no,
                customer=customer,
                subtotal=subtotal,
                discount=discount,
                tax=tax,
                total=total,
                payment_method=payment_method,
                amount_tendered=amount_tendered,
                change_amount=change_amount,
                cashier=request.user,
                created_by=request.user,
                notes=notes
            )

            # Process items, deduct stock, and log inventory movements
            for item in items_data:
                p_id = item.get('product_id')
                qty = int(item.get('quantity', 1))
                unit_price = Decimal(str(item.get('price', 0)))
                line_total = unit_price * qty

                product = Product.objects.select_for_update().get(id=p_id)

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    product_name=product.name,
                    quantity=qty,
                    unit_price=unit_price,
                    total=line_total
                )

                # Reduce Stock
                prev_stock = product.stock
                product.stock -= qty
                product.save()

                # Log Stock Movement
                StockMovement.objects.create(
                    product=product,
                    movement_type='sale',
                    quantity=qty,
                    previous_stock=prev_stock,
                    new_stock=product.stock,
                    reference=invoice_no,
                    notes=f"Sold via POS (Invoice #{invoice_no})",
                    created_by=request.user
                )

            return JsonResponse({
                'success': True,
                'sale_id': sale.id,
                'invoice_number': sale.invoice_number,
                'total': float(sale.total),
                'change_amount': float(sale.change_amount),
                'invoice_url': f"/sales/{sale.id}/invoice/"
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def sales_list(request):
    sales = Sale.objects.filter(cashier=request.user).select_related('customer', 'cashier').prefetch_related('items').order_by('-created_at')

    query = request.GET.get('q', '').strip()
    payment_method = request.GET.get('payment_method')
    date_filter = request.GET.get('date')

    if query:
        sales = sales.filter(
            Q(invoice_number__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(customer__phone__icontains=query)
        )
    if payment_method:
        sales = sales.filter(payment_method=payment_method)
    if date_filter:
        sales = sales.filter(created_at__date=date_filter)

    total_revenue = sales.aggregate(Sum('total'))['total__sum'] or 0
    total_sales_count = sales.count()

    return render(request, 'sales/sales.html', {
        'sales': sales,
        'total_revenue': total_revenue,
        'total_sales_count': total_sales_count,
        'query': query,
        'selected_payment': payment_method,
        'date_filter': date_filter
    })

@login_required
def invoice_detail(request, pk):
    sale = get_object_or_404(Sale.objects.filter(cashier=request.user).select_related('customer', 'cashier').prefetch_related('items__product'), pk=pk)
    return render(request, 'sales/invoice.html', {
        'sale': sale,
        'print_mode': request.GET.get('print', False)
    })
