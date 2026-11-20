from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from .models import Product, Category
from inventory.models import StockMovement
import uuid

@login_required
def product_list(request):
    categories = Category.objects.all()
    products = Product.objects.select_related('category').filter(is_active=True, created_by=request.user)

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    filter_low_stock = request.GET.get('low_stock', '')

    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(sku__icontains=query) | 
            Q(barcode__icontains=query)
        )
    if category_id:
        products = products.filter(category_id=category_id)
    if filter_low_stock == '1':
        # stock <= minimum_stock
        products = [p for p in products if p.is_low_stock]

    return render(request, 'products/list.html', {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'filter_low_stock': filter_low_stock
    })

@login_required
def product_add(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        sku = request.POST.get('sku', '').strip() or f"SKU-{uuid.uuid4().hex[:6].upper()}"
        barcode = request.POST.get('barcode', '').strip() or sku
        category_id = request.POST.get('category')
        purchase_price = request.POST.get('purchase_price', 0) or 0
        selling_price = request.POST.get('selling_price', 0) or 0
        try:
            stock = int(request.POST.get('stock', 0) or 0)
        except (ValueError, TypeError):
            stock = 0
        try:
            minimum_stock = int(request.POST.get('minimum_stock', 5) or 5)
        except (ValueError, TypeError):
            minimum_stock = 5
        image = request.FILES.get('image')

        category = Category.objects.filter(id=category_id).first() if category_id else None

        if Product.objects.filter(sku=sku).exists():
            messages.error(request, f"SKU '{sku}' already exists.")
            return render(request, 'products/add.html', {'categories': categories})

        product = Product.objects.create(
            name=name,
            sku=sku,
            barcode=barcode,
            category=category,
            purchase_price=purchase_price,
            selling_price=selling_price,
            stock=stock,
            minimum_stock=minimum_stock,
            image=image,
            created_by=request.user
        )

        if stock > 0:
            StockMovement.objects.create(
                product=product,
                movement_type='in',
                quantity=stock,
                previous_stock=0,
                new_stock=stock,
                reference='INITIAL-STOCK',
                notes='Initial stock on product creation',
                created_by=request.user
            )

        messages.success(request, f"Product '{product.name}' added successfully.")
        return redirect('product_list')

    return render(request, 'products/add.html', {'categories': categories})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()

    if request.method == 'POST':
        product.name = request.POST.get('name', product.name)
        product.sku = request.POST.get('sku', product.sku)
        product.barcode = request.POST.get('barcode', product.barcode)
        category_id = request.POST.get('category')
        product.category = Category.objects.filter(id=category_id).first() if category_id else None
        product.purchase_price = request.POST.get('purchase_price', product.purchase_price)
        product.selling_price = request.POST.get('selling_price', product.selling_price)
        product.minimum_stock = int(request.POST.get('minimum_stock', product.minimum_stock))
        
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')

        product.save()
        messages.success(request, f"Product '{product.name}' updated successfully.")
        return redirect('product_list')

    return render(request, 'products/edit.html', {'product': product, 'categories': categories})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.is_active = False # soft delete
        product.save()
        messages.success(request, f"Product '{product.name}' was removed.")
    return redirect('product_list')

@login_required
def category_list(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        if name and not Category.objects.filter(name__iexact=name).exists():
            Category.objects.create(name=name, description=description)
            messages.success(request, f"Category '{name}' created.")
        else:
            messages.error(request, "Category already exists or invalid name.")
        return redirect('category_list')

    categories = Category.objects.all()
    return render(request, 'products/categories.html', {'categories': categories})

@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, f"Category '{category.name}' deleted.")
    return redirect('category_list')

@login_required
def api_product_search(request):
    """JSON API endpoint for fast product search & barcode scan in POS"""
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()

    products = Product.objects.filter(is_active=True, created_by=request.user)
    if category_id:
        products = products.filter(category_id=category_id)
    if q:
        products = products.filter(
            Q(name__icontains=q) | 
            Q(sku__icontains=q) | 
            Q(barcode__iexact=q)
        )

    data = []
    for p in products[:50]:
        data.append({
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'barcode': p.barcode or '',
            'price': float(p.selling_price),
            'stock': p.stock,
            'category': p.category.name if p.category else 'Uncategorized',
            'image_url': p.image.url if p.image else '',
            'is_low_stock': p.is_low_stock
        })
    return JsonResponse({'products': data})

@login_required
def print_barcode(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if not product.barcode:
        product.save() # auto-generates if missing

    import io
    import barcode
    from barcode.writer import ImageWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Generate barcode image in memory (with ReportLab built-in fallback)
    try:
        import barcode
        from barcode.writer import ImageWriter
        EAN = barcode.get_barcode_class('code128')
        ean = EAN(product.barcode, writer=ImageWriter())
        buffer = io.BytesIO()
        ean.write(buffer, options={"write_text": False, "module_width": 0.2, "module_height": 8.0, "quiet_zone": 1.0})
        buffer.seek(0)
        img = ImageReader(buffer)
        p.drawImage(img, label_width/2.0 - 25*mm, 12*mm, width=50*mm, height=15*mm, preserveAspectRatio=False)
    except Exception:
        from reportlab.graphics.barcode import createBarcodeDrawing
        drawing = createBarcodeDrawing('Code128', value=product.barcode, width=50*mm, height=15*mm, humanReadable=False)
        drawing.drawOn(p, label_width/2.0 - 25*mm, 12*mm)
    
    # Barcode number
    p.setFont("Helvetica", 8)
    p.drawCentredString(label_width / 2.0, 7*mm, product.barcode)
    
    p.setFont("Helvetica-Bold", 10)
    p.drawCentredString(label_width / 2.0, 3*mm, f"Rs. {product.selling_price}")
    
    p.showPage()
    p.save()
    return response

@login_required
def barcode_list(request):
    products = Product.objects.filter(is_active=True, created_by=request.user)
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(sku__icontains=query) | 
            Q(barcode__icontains=query)
        )
    return render(request, 'products/barcode_list.html', {
        'products': products[:50],  # Limit to 50 for performance, usually enough for search
        'query': query
    })

@login_required
def print_qrcode(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if not product.barcode:
        product.save()

    import io
    import qrcode
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=0,
    )
    qr.add_data(product.barcode)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img_qr.save(buffer, format="PNG")
    buffer.seek(0)
    
    # Label size: 70mm x 50mm (or any size they are using)
    label_width, label_height = 50*mm, 50*mm
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="qrcode_{product.barcode}.pdf"'
    
    p = canvas.Canvas(response, pagesize=(label_width, label_height))
    
    # Just the QR Code
    img = ImageReader(buffer)
    # Draw QR code filling the whole area with a small padding
    padding = 2*mm
    qr_size = label_width - 2*padding
    p.drawImage(img, padding, padding, width=qr_size, height=qr_size, preserveAspectRatio=True)
    
    p.showPage()
    p.save()
    return response

@login_required
def qrcode_image(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if not product.barcode:
        product.save()

    import io
    import qrcode

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=0,
    )
    qr.add_data(product.barcode)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    response = HttpResponse(content_type="image/png")
    img_qr.save(response, "PNG")
    return response

@login_required
def qrcode_list(request):
    products = Product.objects.filter(is_active=True, created_by=request.user)
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(sku__icontains=query) | 
            Q(barcode__icontains=query)
        )
    return render(request, 'products/qrcode_list.html', {
        'products': products[:50],
        'query': query
    })

@login_required
def label_list(request):
    products = Product.objects.filter(is_active=True, created_by=request.user)
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(sku__icontains=query) | 
            Q(barcode__icontains=query)
        )
    return render(request, 'products/label_list.html', {
        'products': products[:50],
        'query': query
    })

@login_required
def print_label(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    
    # Label size: 70mm x 50mm
    label_width, label_height = 70*mm, 50*mm
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="label_{product.sku}.pdf"'
    
    p = canvas.Canvas(response, pagesize=(label_width, label_height))
    
    # Draw border
    p.setLineWidth(0.5)
    p.rect(2*mm, 2*mm, label_width - 4*mm, label_height - 4*mm)
    
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(label_width / 2.0, label_height - 12*mm, f"{product.name[:35]}")
    
    p.setFont("Helvetica", 10)
    p.drawCentredString(label_width / 2.0, label_height - 22*mm, f"SKU: {product.sku}")
    if product.category:
        p.drawCentredString(label_width / 2.0, label_height - 30*mm, f"Cat: {product.category.name}")
        
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(label_width / 2.0, 10*mm, f"Price: Rs. {product.selling_price}")
    
    p.showPage()
    p.save()
    return response
