from django.db import models
from django.conf import settings
from products.models import Product
from suppliers.models import Supplier
import uuid

class Purchase(models.Model):
    STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('pending', 'Pending'),
    )
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases')
    reference_no = models.CharField(max_length=50, unique=True, db_index=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='paid')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"PO #{self.reference_no} - Rs. {self.total}"

    @classmethod
    def generate_reference_no(cls):
        import datetime
        today_str = datetime.date.today().strftime('%Y%m%d')
        random_suffix = str(uuid.uuid4().hex[:6]).upper()
        return f"PO-{today_str}-{random_suffix}"

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='purchase_items')
    quantity = models.IntegerField(default=1)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} in PO #{self.purchase.reference_no}"
