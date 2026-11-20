from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0003_softwarelicense'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_qr_data', models.TextField(default='Kelra Subscription Payment', help_text='Text or payment address encoded into the fallback QR code.')),
                ('payment_qr_image', models.FileField(blank=True, help_text='Optional payment QR image. If empty, a QR is generated from the payment data.', null=True, upload_to='payment_settings/')),
                ('payment_name', models.CharField(default='Kelra Payments', max_length=120)),
                ('payment_instructions', models.TextField(blank=True, default='Scan the QR, complete payment, and upload the payment screenshot below.')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Payment Settings',
                'verbose_name_plural': 'Payment Settings',
            },
        ),
        migrations.CreateModel(
            name='UpgradeRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan', models.CharField(choices=[('starter', 'Starter (Rs. 999/mo)'), ('business', 'Business (Rs. 2,499/mo)'), ('enterprise', 'Enterprise (Custom)')], max_length=50)),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('payment_reference', models.CharField(blank=True, max_length=120)),
                ('payment_screenshot', models.FileField(upload_to='subscription_payments/')),
                ('status', models.CharField(choices=[('pending', 'Pending Review'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('admin_note', models.TextField(blank=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_upgrade_requests', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='upgrade_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]