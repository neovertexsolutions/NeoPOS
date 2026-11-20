from django.core.management.base import BaseCommand
from accounts.models import User
from products.models import Category, Product
from customers.models import Customer
from suppliers.models import Supplier
from expenses.models import ExpenseCategory, Expense
from sales.models import Sale, SaleItem
from purchases.models import Purchase, PurchaseItem
from inventory.models import StockMovement
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta

class Command(BaseCommand):
    help = "Seed database with demo data (users, products, inventory, customers, suppliers, expenses, sales)"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # 1. Users
        users_info = [
            ('admin', 'admin123', 'admin', 'System', 'Admin', '9800000001'),
            ('manager', 'manager123', 'manager', 'Store', 'Manager', '9800000002'),
            ('cashier', 'cashier123', 'cashier', 'John', 'Cashier', '9800000003'),
        ]

        admin_user = None
        for username, password, role, fname, lname, phone in users_info:
            user = User.objects.filter(username=username).first()
            if not user:
                if role == 'admin':
                    user = User.objects.create_superuser(
                        username=username,
                        password=password,
                        email=f"{username}@pos.local",
                        role=role,
                        first_name=fname,
                        last_name=lname,
                        phone=phone
                    )
                else:
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        email=f"{username}@pos.local",
                        role=role,
                        first_name=fname,
                        last_name=lname,
                        phone=phone
                    )
                self.stdout.write(f"Created user: {username} ({role})")
            if role == 'admin':
                admin_user = user

        # 2. Categories
        categories_data = [
            ("Beverages", "Cold drinks, juices, energy drinks, tea, coffee"),
            ("Snacks", "Chips, biscuits, chocolates, cookies"),
            ("Grocery", "Rice, noodles, pasta, flour, oil, spices"),
            ("Bakery", "Fresh bread, cakes, buns, pastries"),
            ("Personal Care", "Soaps, shampoos, toothpaste, sanitizers"),
        ]
        cat_map = {}
        for cname, cdesc in categories_data:
            cat, _ = Category.objects.get_or_create(name=cname, defaults={'description': cdesc})
            cat_map[cname] = cat

        # 3. Products
        products_data = [
            ("Coca Cola 500ml", "SKU-BEV-001", "8901234001", "Beverages", 40.00, 50.00, 48, 10),
            ("Pepsi 500ml", "SKU-BEV-002", "8901234002", "Beverages", 38.00, 50.00, 35, 10),
            ("Red Bull 250ml", "SKU-BEV-003", "8901234003", "Beverages", 120.00, 160.00, 15, 5),
            ("Mineral Water 1L", "SKU-BEV-004", "8901234004", "Beverages", 15.00, 25.00, 80, 20),
            ("Lays Classic Salted", "SKU-SNK-001", "8901234005", "Snacks", 30.00, 40.00, 60, 15),
            ("Doritos Nacho Cheese", "SKU-SNK-002", "8901234006", "Snacks", 45.00, 60.00, 25, 10),
            ("Oreo Cookies 120g", "SKU-SNK-003", "8901234007", "Snacks", 35.00, 50.00, 4, 10), # Low stock demo!
            ("KitKat 4 Finger", "SKU-SNK-004", "8901234008", "Snacks", 40.00, 55.00, 3, 8),   # Low stock demo!
            ("Instant Noodles 75g", "SKU-GRO-001", "8901234009", "Grocery", 18.00, 25.00, 120, 25),
            ("Basmati Rice 5kg", "SKU-GRO-002", "8901234010", "Grocery", 550.00, 720.00, 18, 5),
            ("Sunflower Oil 1L", "SKU-GRO-003", "8901234011", "Grocery", 180.00, 230.00, 22, 6),
            ("Sliced White Bread", "SKU-BAK-001", "8901234012", "Bakery", 40.00, 60.00, 12, 5),
            ("Chocolate Muffin", "SKU-BAK-002", "8901234013", "Bakery", 45.00, 70.00, 8, 4),
            ("Dove Soap Bar 100g", "SKU-PER-001", "8901234014", "Personal Care", 50.00, 75.00, 30, 8),
            ("Colgate Toothpaste", "SKU-PER-002", "8901234015", "Personal Care", 75.00, 110.00, 2, 6), # Low stock demo!
        ]

        created_products = []
        for name, sku, barcode, cname, buy_p, sell_p, stock, min_stock in products_data:
            prod, created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    'name': name,
                    'barcode': barcode,
                    'category': cat_map.get(cname),
                    'purchase_price': Decimal(str(buy_p)),
                    'selling_price': Decimal(str(sell_p)),
                    'stock': stock,
                    'minimum_stock': min_stock
                }
            )
            created_products.append(prod)
            if created and stock > 0:
                StockMovement.objects.create(
                    product=prod,
                    movement_type='in',
                    quantity=stock,
                    previous_stock=0,
                    new_stock=stock,
                    reference='INIT-SEED',
                    notes='Initial seed stock',
                    created_by=admin_user
                )

        # 4. Customers
        customers_data = [
            ("Walk-in Customer", "9810000000", "walkin@pos.local", "In Store"),
            ("Aarav Sharma", "9841234567", "aarav@gmail.com", "Kathmandu, New Road"),
            ("Priya Patel", "9851122334", "priya.patel@gmail.com", "Lalitpur, Jhamsikhel"),
            ("Rohan Thapa", "9803344556", "rohan.t@yahoo.com", "Pokhara, Lakeside"),
        ]
        created_customers = []
        for cname, phone, email, addr in customers_data:
            cust, _ = Customer.objects.get_or_create(name=cname, defaults={'phone': phone, 'email': email, 'address': addr})
            created_customers.append(cust)

        # 5. Suppliers
        suppliers_data = [
            ("Apex Wholesale Distributors", "01-4223344", "orders@apexwholesale.com", "Industrial Zone 1"),
            ("Metro Food & Beverages", "01-5544332", "sales@metrobev.com", "Ring Road Hub"),
            ("Global FMCG Logistics", "01-6677889", "contact@globalfmcg.com", "Warehouse 12B"),
        ]
        for sname, phone, email, addr in suppliers_data:
            Supplier.objects.get_or_create(name=sname, defaults={'phone': phone, 'email': email, 'address': addr})

        # 6. Expenses
        exp_cats = ["Electricity & Water", "Store Rent", "Packaging & Bags", "Store Maintenance", "Staff Meals"]
        created_exp_cats = []
        for ec in exp_cats:
            cat, _ = ExpenseCategory.objects.get_or_create(name=ec)
            created_exp_cats.append(cat)

        today = timezone.now().date()
        for i in range(10):
            day = today - timedelta(days=i)
            Expense.objects.get_or_create(
                date=day,
                category=random.choice(created_exp_cats),
                defaults={
                    'amount': Decimal(str(random.choice([250, 450, 600, 1200, 350]))),
                    'description': f"Daily operational cost for {day.strftime('%b %d')}",
                    'created_by': admin_user
                }
            )

        # 7. Seed Sample Sales across past 7 days for rich Dashboard Charts
        if Sale.objects.count() < 10:
            for i in range(7, -1, -1):
                sale_date = timezone.now() - timedelta(days=i, hours=random.randint(1, 8))
                num_sales_day = random.randint(2, 5)

                for _ in range(num_sales_day):
                    cust = random.choice(created_customers)
                    inv_no = Sale.generate_invoice_number()
                    pay_method = random.choice(['cash', 'card', 'qr'])

                    # Pick 1-3 random products
                    sample_prods = random.sample(created_products, k=random.randint(1, 3))
                    subtotal = Decimal('0.00')

                    items_to_create = []
                    for sp in sample_prods:
                        qty = random.randint(1, 3)
                        line_total = sp.selling_price * qty
                        subtotal += line_total
                        items_to_create.append((sp, qty, sp.selling_price, line_total))

                    discount = Decimal('0.00') if subtotal < 200 else Decimal('20.00')
                    tax = (subtotal - discount) * Decimal('0.05')
                    total = subtotal - discount + tax
                    tendered = total if pay_method != 'cash' else total + Decimal('50.00')
                    change = Decimal('0.00') if pay_method != 'cash' else Decimal('50.00')

                    sale = Sale.objects.create(
                        invoice_number=inv_no,
                        customer=cust,
                        subtotal=subtotal,
                        discount=discount,
                        tax=tax,
                        total=total,
                        payment_method=pay_method,
                        amount_tendered=tendered,
                        change_amount=change,
                        cashier=admin_user,
                        created_at=sale_date
                    )
                    # Override created_at for historical charts
                    Sale.objects.filter(id=sale.id).update(created_at=sale_date)

                    for sp, qty, price, lt in items_to_create:
                        SaleItem.objects.create(
                            sale=sale,
                            product=sp,
                            product_name=sp.name,
                            quantity=qty,
                            unit_price=price,
                            total=lt
                        )

        self.stdout.write(self.style.SUCCESS("Demo database successfully seeded with users, products, sales, customers, suppliers, and expenses!"))
