from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from .models import Customer
import json

@login_required
def customer_list(request):
    query = request.GET.get('q', '').strip()
    customers = Customer.objects.filter(created_by=request.user).annotate(
        total_orders=Count('sales'),
        total_spent=Sum('sales__total')
    )
    if query:
        customers = customers.filter(
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
            Customer.objects.create(name=name, phone=phone, email=email, address=address, created_by=request.user)
            messages.success(request, f"Customer '{name}' added successfully.")
            return redirect('customer_list')

    return render(request, 'customers/customers.html', {
        'customers': customers,
        'query': query
    })

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    sales = customer.sales.all().prefetch_related('items').order_by('-created_at')
    total_spent = sales.aggregate(Sum('total'))['total__sum'] or 0
    return render(request, 'customers/detail.html', {
        'customer': customer,
        'sales': sales,
        'total_spent': total_spent,
    })

@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.name = request.POST.get('name', customer.name)
        customer.phone = request.POST.get('phone', customer.phone)
        customer.email = request.POST.get('email', customer.email)
        customer.address = request.POST.get('address', customer.address)
        customer.save()
        messages.success(request, f"Customer '{customer.name}' updated.")
        return redirect('customer_list')
    return render(request, 'customers/edit.html', {'customer': customer})

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, "Customer removed.")
    return redirect('customer_list')

@login_required
def api_customer_create(request):
    """Allows creating a new customer directly from the POS modal"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            phone = data.get('phone', '').strip()
            email = data.get('email', '').strip()
            address = data.get('address', '').strip()

            if not name:
                return JsonResponse({'success': False, 'error': 'Customer name is required.'}, status=400)

            customer = Customer.objects.create(
                name=name,
                phone=phone,
                email=email,
                address=address,
                created_by=request.user
            )
            return JsonResponse({
                'success': True,
                'customer': {
                    'id': customer.id,
                    'name': customer.name,
                    'phone': customer.phone or ''
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid method'}, status=405)
