from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from .models import Supplier

@login_required
def supplier_list(request):
    query = request.GET.get('q', '').strip()
    suppliers = Supplier.objects.annotate(
        total_purchases=Count('purchases'),
        total_spent=Sum('purchases__total')
    )
    if query:
        suppliers = suppliers.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )

    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        address = request.POST.get('address', '')
        if name:
            Supplier.objects.create(name=name, phone=phone, email=email, address=address)
            messages.success(request, f"Supplier '{name}' added successfully.")
            return redirect('supplier_list')

    return render(request, 'suppliers/suppliers.html', {
        'suppliers': suppliers,
        'query': query
    })

@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    purchases = supplier.purchases.all().prefetch_related('items').order_by('-created_at')
    total_spent = purchases.aggregate(Sum('total'))['total__sum'] or 0
    return render(request, 'suppliers/detail.html', {
        'supplier': supplier,
        'purchases': purchases,
        'total_spent': total_spent,
    })

@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.name = request.POST.get('name', supplier.name)
        supplier.phone = request.POST.get('phone', supplier.phone)
        supplier.email = request.POST.get('email', supplier.email)
        supplier.address = request.POST.get('address', supplier.address)
        supplier.save()
        messages.success(request, f"Supplier '{supplier.name}' updated.")
        return redirect('supplier_list')
    return render(request, 'suppliers/edit.html', {'supplier': supplier})

@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, "Supplier removed.")
    return redirect('supplier_list')
