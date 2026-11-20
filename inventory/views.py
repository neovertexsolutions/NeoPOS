from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from products.models import Product, Category
from .models import StockMovement

@login_required
def inventory_list(request):
    categories = Category.objects.all()
    products = Product.objects.select_related('category').filter(is_active=True, created_by=request.user).order_by('name')

    filter_type = request.GET.get('filter', 'all')
    category_id = request.GET.get('category', '')
    query = request.GET.get('q', '').strip()

    if category_id:
        products = products.filter(category_id=category_id)
    if query:
        products = products.filter(name__icontains=query) | products.filter(sku__icontains=query)

    if filter_type == 'low':
        # stock <= minimum_stock and stock > 0
        products = [p for p in products if p.stock <= p.minimum_stock and p.stock > 0]
    elif filter_type == 'out':
        products = [p for p in products if p.stock <= 0]

    # Quick summaries
    all_active = Product.objects.filter(is_active=True, created_by=request.user)
    total_items = all_active.count()
    low_stock_count = sum(1 for p in all_active if p.stock <= p.minimum_stock and p.stock > 0)
    out_of_stock_count = sum(1 for p in all_active if p.stock <= 0)
    total_stock_value = sum(p.stock * p.selling_price for p in all_active)

    return render(request, 'inventory/inventory.html', {
        'products': products,
        'categories': categories,
        'total_items': total_items,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_stock_value': total_stock_value,
        'filter_type': filter_type,
        'selected_category': category_id,
        'query': query
    })

@login_required
def stock_adjustment(request):
    """Handles manual Stock In, Stock Out, or Direct Stock Adjustment"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action_type = request.POST.get('action_type') # 'in', 'out', 'adjustment'
        try:
            quantity = int(request.POST.get('quantity', 0) or 0)
        except (ValueError, TypeError):
            quantity = 0
        reason = request.POST.get('reason', '').strip()
        reference = request.POST.get('reference', '').strip() or 'MANUAL-ADJUST'

        product = get_object_or_404(Product, pk=product_id)

        with transaction.atomic():
            prev_stock = product.stock
            if action_type == 'in':
                if quantity <= 0:
                    messages.error(request, "Quantity must be greater than zero.")
                    return redirect('inventory_list')
                new_stock = prev_stock + quantity
                movement_type = 'in'
            elif action_type == 'out':
                if quantity <= 0:
                    messages.error(request, "Quantity must be greater than zero.")
                    return redirect('inventory_list')
                if quantity > prev_stock:
                    messages.error(request, f"Cannot remove {quantity} items. Only {prev_stock} available in stock.")
                    return redirect('inventory_list')
                new_stock = prev_stock - quantity
                movement_type = 'out'
            elif action_type == 'adjustment':
                new_stock = quantity
                if new_stock < 0:
                    messages.error(request, "Stock cannot be negative.")
                    return redirect('inventory_list')
                movement_type = 'adjustment'
                quantity = abs(new_stock - prev_stock)
            else:
                messages.error(request, "Invalid action type.")
                return redirect('inventory_list')

            product.stock = new_stock
            product.save()

            StockMovement.objects.create(
                product=product,
                movement_type=movement_type,
                quantity=quantity,
                previous_stock=prev_stock,
                new_stock=new_stock,
                reference=reference,
                notes=reason,
                created_by=request.user
            )

            messages.success(request, f"Stock for '{product.name}' updated successfully: {prev_stock} -> {new_stock}.")
            return redirect('inventory_list')

    return redirect('inventory_list')

@login_required
def movement_history(request):
    movements_list = StockMovement.objects.select_related('product', 'created_by').filter(product__created_by=request.user).order_by('-created_at')
    
    movement_type = request.GET.get('type')
    product_id = request.GET.get('product')

    if movement_type:
        movements_list = movements_list.filter(movement_type=movement_type)
    if product_id:
        movements_list = movements_list.filter(product_id=product_id)

    paginator = Paginator(movements_list, 25)
    page_number = request.GET.get('page')
    movements = paginator.get_page(page_number)
    products = Product.objects.filter(is_active=True, created_by=request.user).order_by('name')

    return render(request, 'inventory/history.html', {
        'movements': movements,
        'products': products,
        'selected_type': movement_type,
        'selected_product': product_id
    })
