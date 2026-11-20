from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Purchase, PurchaseItem
from suppliers.models import Supplier
from products.models import Product
from inventory.models import StockMovement
from decimal import Decimal
import json

@login_required
def purchases_list(request):
    purchases = Purchase.objects.filter(created_by=request.user).select_related('supplier', 'created_by').prefetch_related('items').order_by('-created_at')
    return render(request, 'purchases/purchases.html', {'purchases': purchases})

@login_required
def purchase_add(request):
    suppliers = Supplier.objects.all()
    products = Product.objects.filter(is_active=True, created_by=request.user).order_by('name')

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier_id')
        payment_status = request.POST.get('payment_status', 'paid')
        notes = request.POST.get('notes', '')
        items_json = request.POST.get('items_json', '[]')

        supplier = Supplier.objects.filter(id=supplier_id).first() if supplier_id else None
        
        try:
            items_data = json.loads(items_json)
        except Exception:
            items_data = []

        if not items_data:
            messages.error(request, "Please add at least one product to the purchase order.")
            return render(request, 'purchases/add.html', {'suppliers': suppliers, 'products': products})

        with transaction.atomic():
            ref_no = Purchase.generate_reference_no()
            purchase = Purchase.objects.create(
                supplier=supplier,
                reference_no=ref_no,
                payment_status=payment_status,
                notes=notes,
                created_by=request.user,
                total=0
            )

            grand_total = Decimal('0.00')

            for item in items_data:
                product_id = item.get('product_id')
                qty = int(item.get('quantity', 1))
                price = Decimal(str(item.get('price', 0)))
                line_total = price * qty
                grand_total += line_total

                product = Product.objects.select_for_update().get(id=product_id)
                
                # Create Purchase Item
                PurchaseItem.objects.create(
                    purchase=purchase,
                    product=product,
                    quantity=qty,
                    purchase_price=price,
                    total=line_total
                )

                # Automatically Increase Stock
                prev_stock = product.stock
                product.stock += qty
                product.purchase_price = price # update latest purchase cost
                product.save()

                # Log Stock Movement
                StockMovement.objects.create(
                    product=product,
                    movement_type='purchase',
                    quantity=qty,
                    previous_stock=prev_stock,
                    new_stock=product.stock,
                    reference=ref_no,
                    notes=f"Stock In from Purchase Order #{ref_no}",
                    created_by=request.user
                )

            purchase.total = grand_total
            purchase.save()

            messages.success(request, f"Purchase Order #{ref_no} recorded successfully. Total: Rs. {grand_total:.2f}. Stock updated!")
            return redirect('purchases_list')

    return render(request, 'purchases/add.html', {'suppliers': suppliers, 'products': products})

@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(Purchase.objects.select_related('supplier', 'created_by').prefetch_related('items__product'), pk=pk)
    return render(request, 'purchases/detail.html', {'purchase': purchase})
