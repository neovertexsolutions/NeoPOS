from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
    )
    PLAN_CHOICES = (
        ('starter', 'Starter (Rs. 999/mo)'),
        ('business', 'Business (Rs. 2,499/mo)'),
        ('enterprise', 'Enterprise (Custom)'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cashier')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    store_name = models.CharField(max_length=200, blank=True, null=True, default="My Retail Store")
    plan = models.CharField(max_length=50, choices=PLAN_CHOICES, default='business')
    trial_ends_at = models.DateField(blank=True, null=True)

    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    @property
    def is_manager(self):
        return self.role in ['admin', 'manager'] or self.is_superuser

    @property
    def is_cashier(self):
        return self.role in ['admin', 'manager', 'cashier']

    @property
    def days_left_trial(self):
        if self.trial_ends_at:
            delta = (self.trial_ends_at - timezone.now().date()).days
            return max(0, delta)
        return 14
        

    @property
    def license_key(self):
        import hashlib
        seed = f"{self.id}-{self.username}-{self.store_name}-SPOS"
        digest = hashlib.sha256(seed.encode()).hexdigest().upper()
        return f"SPOS-2026-{digest[:4]}-{digest[4:8]}-{digest[8:12]}"

    @property
    def license_status(self):
        today = timezone.now().date()
        if not self.trial_ends_at:
            return "Active (Lifetime / Permanent)"
        if self.trial_ends_at >= today:
            days = (self.trial_ends_at - today).days
            return f"Active (14-Day Trial: {days} days left)"
        days_ago = (today - self.trial_ends_at).days
        return f"Expired ({days_ago} days ago)"

    @property
    def has_active_access(self):
        if not self.is_active:
            return False
        return self.trial_ends_at is None or self.trial_ends_at >= timezone.now().date()

    def save(self, *args, **kwargs):
        if not self.trial_ends_at and self.role == 'admin':
            self.trial_ends_at = timezone.now().date() + timedelta(days=14)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


import secrets

class SoftwareLicense(models.Model):
    PLAN_CHOICES = (
        ('starter', 'Starter Plan (Rs. 999/mo)'),
        ('business', 'Business Plan (Rs. 2,499/mo)'),
        ('enterprise', 'Enterprise Plan (Custom)'),
    )
    DURATION_CHOICES = (
        ('14', '14 Days Free Trial'),
        ('30', '1 Month (30 Days)'),
        ('90', '3 Months (Quarterly)'),
        ('180', '6 Months (Half-Yearly)'),
        ('365', '1 Year (Annual)'),
        ('lifetime', 'Lifetime / Permanent (No Expiry)'),
    )

    license_key = models.CharField(max_length=60, unique=True, db_index=True)
    plan = models.CharField(max_length=50, choices=PLAN_CHOICES, default='business')
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES, default='365')
    client_name = models.CharField(max_length=200, blank=True, null=True, help_text="Client or Store Name")
    assigned_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='software_licenses')
    is_active = models.BooleanField(default=True, help_text="Active / Valid license")
    is_redeemed = models.BooleanField(default=False, help_text="Has this license been activated?")
    redeemed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Software License"
        verbose_name_plural = "Software Licenses"

    @classmethod
    def generate_unique_key(cls, plan='business', duration='365'):
        prefix_map = {'starter': 'STR', 'business': 'BUS', 'enterprise': 'ENT'}
        dur_map = {'14': '14D', '30': '1M', '90': '3M', '180': '6M', '365': '1Y', 'lifetime': 'LIFE'}
        p_code = prefix_map.get(plan, 'POS')
        d_code = dur_map.get(duration, 'KEY')
        rand1 = secrets.token_hex(2).upper()
        rand2 = secrets.token_hex(2).upper()
        rand3 = secrets.token_hex(2).upper()
        key = f"SPOS-{p_code}-{d_code}-{rand1}-{rand2}-{rand3}"
        return key

    def __str__(self):
        return f"{self.license_key} [{self.get_plan_display()}]"


class LicenseKeyOption(models.Model):
    plan = models.CharField(max_length=50, choices=SoftwareLicense.PLAN_CHOICES)
    duration = models.CharField(max_length=20, choices=SoftwareLicense.DURATION_CHOICES)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['plan', 'id']
        constraints = [
            models.UniqueConstraint(fields=('plan', 'duration'), name='unique_license_key_option'),
        ]
        verbose_name = 'License Key Type'
        verbose_name_plural = 'License Key Types'

    def __str__(self):
        return f'{self.get_plan_display()} - {self.get_duration_display()}'


class PaymentSettings(models.Model):
    payment_qr_data = models.TextField(
        default='Kelra Subscription Payment',
        help_text='Text or payment address encoded into the fallback QR code.'
    )
    payment_qr_image = models.FileField(
        upload_to='payment_settings/',
        blank=True,
        null=True,
        help_text='Optional payment QR image. If empty, a QR is generated from the payment data.'
    )
    payment_name = models.CharField(max_length=120, default='Kelra Payments')
    payment_instructions = models.TextField(
        blank=True,
        default='Scan the QR, complete payment, and upload the payment screenshot below.'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Payment Settings'
        verbose_name_plural = 'Payment Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.payment_name


class UpgradeRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    PLAN_PRICES = {
        'starter': 999,
        'business': 2499,
        'enterprise': 0,
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upgrade_requests')
    plan = models.CharField(max_length=50, choices=User.PLAN_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_reference = models.CharField(max_length=120, blank=True)
    payment_screenshot = models.FileField(upload_to='subscription_payments/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_upgrade_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def plan_price(self):
        return self.PLAN_PRICES.get(self.plan, 0)

    def __str__(self):
        return f'{self.user.username} - {self.get_plan_display()} ({self.get_status_display()})'
