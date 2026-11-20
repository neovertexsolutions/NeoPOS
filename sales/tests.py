from django.test import TestCase, Client, RequestFactory
from django.conf import settings
from django.urls import reverse, resolve
from accounts.models import User
from products.models import Product, Category
from customers.models import Customer
from sales.models import Sale, SaleItem
from sales.views import pos_terminal
from purchases.models import Purchase, PurchaseItem
from inventory.models import StockMovement
from decimal import Decimal
import re
import json

class POSTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='testadmin',
            password='password123',
            role='admin'
        )
        self.category = Category.objects.create(name='Snacks')
        self.product = Product.objects.create(
            name='Test Biscuit',
            sku='SKU-TEST-001',
            barcode='1234567890',
            category=self.category,
            purchase_price=Decimal('20.00'),
            selling_price=Decimal('30.00'),
            stock=10,
            minimum_stock=3
        )
        self.customer = Customer.objects.create(name='Test Customer', phone='9800000000')

    def test_marketing_landing_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kelra')

    def test_dashboard_authenticated(self):
        self.client.login(username='testadmin', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Store Dashboard')

    def test_pos_sale_checkout_api(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        pos_request = RequestFactory().get(reverse('pos_terminal'))
        pos_request.user = self.admin
        pos_request.resolver_match = resolve(reverse('pos_terminal'))
        pos_response = pos_terminal(pos_request)
        self.assertEqual(pos_response.status_code, 200)
        token_match = re.search(rb'<meta name="csrf-token" content="([^"]+)"', pos_response.content)
        self.assertIsNotNone(token_match)
        csrf_token = token_match.group(1).decode()
        self.assertIn(settings.CSRF_COOKIE_NAME, pos_response.cookies)
        client.cookies[settings.CSRF_COOKIE_NAME] = csrf_token
        initial_stock = self.product.stock

        payload = {
            'customer_id': self.customer.id,
            'payment_method': 'cash',
            'subtotal': 60.00,
            'discount': 0.00,
            'tax': 3.00,
            'total': 63.00,
            'amount_tendered': 100.00,
            'change_amount': 37.00,
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 2,
                    'price': 30.00
                }
            ]
        }

        response = client.post(
            reverse('api_process_sale'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total'], 63.00)

        # Verify stock decrement
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - 2)

        # Verify stock movement recorded
        movement = StockMovement.objects.filter(product=self.product, movement_type='sale').first()
        self.assertIsNotNone(movement)
        self.assertEqual(movement.quantity, 2)

    def test_purchase_auto_stock_increment(self):
        self.client.login(username='testadmin', password='password123')
        initial_stock = self.product.stock

        items_json = json.dumps([
            {
                'product_id': self.product.id,
                'quantity': 5,
                'price': 22.00
            }
        ])

        response = self.client.post(reverse('purchase_add'), {
            'payment_status': 'paid',
            'notes': 'Supplier delivery test',
            'items_json': items_json
        })
        self.assertEqual(response.status_code, 302) # Redirects to purchase list

        # Verify stock increment
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock + 5)

    def test_user_dashboard_only_shows_own_data(self):
        other_user = User.objects.create_user(
            username='otheruser',
            password='password123',
            role='admin'
        )
        self.client.login(username='otheruser', password='password123')
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_products_count'], 0)
        self.assertNotContains(response, 'Test Biscuit')
