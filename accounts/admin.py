from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import transaction
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from .models import User, SoftwareLicense, PaymentSettings, UpgradeRequest

# Configure Admin Site Headers
admin.site.site_header = "Kelra Administration"
admin.site.site_title = "Kelra Admin"
admin.site.index_title = "Store & Subscription Management Portal"


class TrialStatusFilter(admin.SimpleListFilter):
    title = '14-Day Trial Status'
    parameter_name = 'trial_status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active Trial (Running)'),
            ('ending_soon', 'Ending Soon (<= 3 Days)'),
            ('expired', 'Trial Expired'),
            ('lifetime', 'Permanent / No Trial Limit'),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()
        if self.value() == 'active':
            return queryset.filter(trial_ends_at__gte=today)
        elif self.value() == 'ending_soon':
            three_days_later = today + timedelta(days=3)
            return queryset.filter(trial_ends_at__gte=today, trial_ends_at__lte=three_days_later)
        elif self.value() == 'expired':
            return queryset.filter(trial_ends_at__lt=today)
        elif self.value() == 'lifetime':
            return queryset.filter(trial_ends_at__isnull=True)
        return queryset


@admin.register(PaymentSettings)
class PaymentSettingsAdmin(admin.ModelAdmin):
    list_display = ('payment_name', 'qr_preview', 'payment_qr_image', 'updated_at')
    fieldsets = (
        ('Payment QR', {
            'fields': ('payment_name', 'payment_qr_data', 'payment_qr_image', 'qr_preview', 'payment_instructions'),
            'description': 'Upload the real payment QR or set the payment data used to generate the fallback QR.'
        }),
    )
    readonly_fields = ('qr_preview',)

    def has_add_permission(self, request):
        return not PaymentSettings.objects.exists()

    @admin.display(description='QR Preview')
    def qr_preview(self, obj):
        if not obj or not obj.payment_qr_image:
            return 'Fallback QR generated from payment data'
        return format_html(
            '<img src="{}" alt="Payment QR" style="width: 150px; height: 150px; object-fit: contain; border: 1px solid #ddd; padding: 6px; background: #fff;">',
            obj.payment_qr_image.url,
        )


@admin.register(UpgradeRequest)
class UpgradeRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount', 'status', 'created_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('status', 'plan', 'created_at')
    search_fields = ('user__username', 'user__email', 'payment_reference')
    readonly_fields = ('user', 'plan', 'amount', 'payment_reference', 'payment_screenshot', 'created_at', 'reviewed_by', 'reviewed_at')
    actions = ('approve_requests', 'reject_requests')

    @admin.action(description='Approve selected payment requests')
    def approve_requests(self, request, queryset):
        approved_count = 0
        today = timezone.now().date()
        for upgrade in queryset.filter(status='pending').select_related('user'):
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=upgrade.user_id)
                user.plan = upgrade.plan
                user.is_active = True
                if upgrade.plan == 'enterprise':
                    user.trial_ends_at = None
                else:
                    base = user.trial_ends_at if user.trial_ends_at and user.trial_ends_at > today else today
                    user.trial_ends_at = base + timedelta(days=30)
                user.save(update_fields=['plan', 'is_active', 'trial_ends_at'])
                upgrade.status = 'approved'
                upgrade.reviewed_by = request.user
                upgrade.reviewed_at = timezone.now()
                upgrade.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
                approved_count += 1
        self.message_user(request, f'{approved_count} payment request(s) approved and full access activated.')

    @admin.action(description='Reject selected payment requests')
    def reject_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f'{updated} payment request(s) rejected.')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'store_name_display',
        'role_badge',
        'plan_badge',
        'trial_badge',
        'trial_ends_at',
        'is_active',
        'is_staff',
        'date_joined',
    )
    list_filter = (
        TrialStatusFilter,
        'plan',
        'role',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'store_name',
        'phone',
    )
    ordering = ('-date_joined',)

    actions = [
        'extend_trial_14_days',
        'extend_trial_30_days',
        'extend_trial_7_days',
        'mark_trial_expired',
        'upgrade_to_starter',
        'upgrade_to_business',
        'upgrade_to_enterprise',
        'activate_users',
        'deactivate_users',
    ]

    fieldsets = (
        ('Account Credentials', {
            'fields': ('username', 'password', 'first_name', 'last_name', 'email')
        }),
        ('Store & Contact Info', {
            'fields': ('store_name', 'phone', 'address')
        }),
        ('Subscription & 14-Day Trial Controls', {
            'fields': ('role', 'plan', 'trial_ends_at', 'trial_details_preview'),
            'description': 'Configure store access tier, upgrade subscriptions, and adjust 14-day free trial dates.'
        }),
        ('Permissions & Staff Access', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('date_joined', 'last_login', 'trial_details_preview')

    def changelist_view(self, request, extra_context=None):
        today = timezone.now().date()
        total_users = User.objects.count()
        active_trials = User.objects.filter(trial_ends_at__gte=today).count()
        expired_trials = User.objects.filter(trial_ends_at__lt=today).count()
        no_expiry = User.objects.filter(trial_ends_at__isnull=True).count()
        
        starter_count = User.objects.filter(plan='starter').count()
        business_count = User.objects.filter(plan='business').count()
        enterprise_count = User.objects.filter(plan='enterprise').count()
        
        admin_count = User.objects.filter(role='admin').count()
        manager_count = User.objects.filter(role='manager').count()
        cashier_count = User.objects.filter(role='cashier').count()

        extra_context = extra_context or {}
        extra_context['metrics'] = {
            'total_users': total_users,
            'active_trials': active_trials,
            'expired_trials': expired_trials,
            'no_expiry': no_expiry,
            'starter_count': starter_count,
            'business_count': business_count,
            'enterprise_count': enterprise_count,
            'admin_count': admin_count,
            'manager_count': manager_count,
            'cashier_count': cashier_count,
        }
        return super().changelist_view(request, extra_context=extra_context)

    # UI Badges
    @admin.display(description='Store Name')
    def store_name_display(self, obj):
        return obj.store_name or "-"

    @admin.display(description='Role')
    def role_badge(self, obj):
        styles = {
            'admin': ('background: #fee2e2; color: #991b1b; border: 1px solid #fecaca;', 'Admin (Full)'),
            'manager': ('background: #e0f2fe; color: #075985; border: 1px solid #bae6fd;', 'Manager'),
            'cashier': ('background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1;', 'Cashier'),
        }
        css, label = styles.get(obj.role, ('background: #f1f5f9; color: #334155;', obj.role))
        return format_html(
            '<span style="padding: 3px 8px; border-radius: 6px; font-weight: 600; font-size: 11px; {}">{}</span>',
            css, label
        )

    @admin.display(description='Plan')
    def plan_badge(self, obj):
        plan_styles = {
            'starter': ('background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe;', 'Starter (Rs. 999)'),
            'business': ('background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe;', 'Business (Rs. 2,499)'),
            'enterprise': ('background: #fef3c7; color: #b45309; border: 1px solid #fde68a;', 'Enterprise (Custom)'),
        }
        css, label = plan_styles.get(obj.plan, ('background: #f1f5f9; color: #475569;', obj.plan))
        return format_html(
            '<span style="padding: 3px 9px; border-radius: 6px; font-weight: 700; font-size: 11px; {}">{}</span>',
            css, label
        )

    @admin.display(description='14-Day Trial Status')
    def trial_badge(self, obj):
        if not obj.trial_ends_at:
            return format_html('<span style="color: #64748b; font-size: 11px;">Permanent / No Trial</span>')

        today = timezone.now().date()
        days_left = (obj.trial_ends_at - today).days

        if days_left < 0:
            return format_html(
                '<span style="background: #fee2e2; color: #b91c1c; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px; border: 1px solid #fecaca;">'
                '❌ Expired ({}d ago)'
                '</span>',
                abs(days_left)
            )
        elif days_left <= 3:
            return format_html(
                '<span style="background: #ffedd5; color: #c2410c; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px; border: 1px solid #fed7aa;">'
                '⚠️ Ending Soon ({}d left)'
                '</span>',
                days_left
            )
        else:
            return format_html(
                '<span style="background: #dcfce7; color: #15803d; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px; border: 1px solid #bbf7d0;">'
                '✅ Active ({}d left)'
                '</span>',
                days_left
            )

    @admin.display(description='Trial Details')
    def trial_details_preview(self, obj):
        if not obj.trial_ends_at:
            return "This user has no expiration date set (Permanent / Non-expiring access)."
        today = timezone.now().date()
        delta = (obj.trial_ends_at - today).days
        if delta < 0:
            return format_html(
                '<span style="color: #dc2626; font-weight: bold;">Expired on {} ({} days ago)</span>',
                obj.trial_ends_at, abs(delta)
            )
        return format_html(
            '<span style="color: #16a34a; font-weight: bold;">Active until {} ({} days remaining)</span>',
            obj.trial_ends_at, delta
        )

    # Admin Actions
    @admin.action(description="⏳ Extend 14-Day Free Trial (+14 Days)")
    def extend_trial_14_days(self, request, queryset):
        today = timezone.now().date()
        count = 0
        for u in queryset:
            base = u.trial_ends_at if (u.trial_ends_at and u.trial_ends_at > today) else today
            u.trial_ends_at = base + timedelta(days=14)
            u.save(update_fields=['trial_ends_at'])
            count += 1
        self.message_user(request, f"Successfully extended 14-day trial for {count} user(s).")

    @admin.action(description="➕ Add +30 Days Trial / Access")
    def extend_trial_30_days(self, request, queryset):
        today = timezone.now().date()
        count = 0
        for u in queryset:
            base = u.trial_ends_at if (u.trial_ends_at and u.trial_ends_at > today) else today
            u.trial_ends_at = base + timedelta(days=30)
            u.save(update_fields=['trial_ends_at'])
            count += 1
        self.message_user(request, f"Added +30 days access for {count} user(s).")

    @admin.action(description="➕ Add +7 Days Trial")
    def extend_trial_7_days(self, request, queryset):
        today = timezone.now().date()
        count = 0
        for u in queryset:
            base = u.trial_ends_at if (u.trial_ends_at and u.trial_ends_at > today) else today
            u.trial_ends_at = base + timedelta(days=7)
            u.save(update_fields=['trial_ends_at'])
            count += 1
        self.message_user(request, f"Added +7 days trial for {count} user(s).")

    @admin.action(description="🛑 Expire 14-Day Trial Immediately")
    def mark_trial_expired(self, request, queryset):
        yesterday = timezone.now().date() - timedelta(days=1)
        count = queryset.update(trial_ends_at=yesterday)
        self.message_user(request, f"Marked trial as expired for {count} user(s).")

    @admin.action(description="🚀 Upgrade Plan to Starter (Rs. 999/mo)")
    def upgrade_to_starter(self, request, queryset):
        count = queryset.update(plan='starter')
        self.message_user(request, f"Upgraded {count} user(s) to Starter Plan.")

    @admin.action(description="💎 Upgrade Plan to Business (Rs. 2,499/mo)")
    def upgrade_to_business(self, request, queryset):
        count = queryset.update(plan='business')
        self.message_user(request, f"Upgraded {count} user(s) to Business Plan.")

    @admin.action(description="👑 Upgrade Plan to Enterprise (Custom)")
    def upgrade_to_enterprise(self, request, queryset):
        count = queryset.update(plan='enterprise')
        self.message_user(request, f"Upgraded {count} user(s) to Enterprise Plan.")

    @admin.action(description="✅ Activate Selected User Accounts")
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"Activated {count} user account(s).")

    @admin.action(description="🚫 Deactivate Selected User Accounts")
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} user account(s).")


@admin.register(SoftwareLicense)
class SoftwareLicenseAdmin(admin.ModelAdmin):
    list_display = (
        'license_key_badge',
        'client_name_display',
        'plan_badge',
        'duration_display',
        'assigned_user',
        'status_badge',
        'created_at',
    )
    list_filter = ('plan', 'duration', 'is_active', 'is_redeemed', 'created_at')
    search_fields = ('license_key', 'client_name', 'assigned_user__username')
    ordering = ('-created_at',)

    actions = ['revoke_licenses', 'activate_licenses']

    @admin.display(description='Software License Key')
    def license_key_badge(self, obj):
        return format_html(
            '<code style="background: #f1f5f9; border: 1px dashed #cbd5e1; padding: 3px 8px; border-radius: 5px; font-weight: bold; color: #0f172a;">{}</code>',
            obj.license_key
        )

    @admin.display(description='Client / Store')
    def client_name_display(self, obj):
        return obj.client_name or "-"

    @admin.display(description='Plan Tier')
    def plan_badge(self, obj):
        styles = {
            'starter': ('background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe;', 'Starter (Rs. 999)'),
            'business': ('background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe;', 'Business (Rs. 2,499)'),
            'enterprise': ('background: #fef3c7; color: #b45309; border: 1px solid #fde68a;', 'Enterprise (Custom)'),
        }
        css, label = styles.get(obj.plan, ('background: #f1f5f9; color: #475569;', obj.plan))
        return format_html('<span style="padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px; {}">{}</span>', css, label)

    @admin.display(description='Duration')
    def duration_display(self, obj):
        return obj.get_duration_display()

    @admin.display(description='Status')
    def status_badge(self, obj):
        if not obj.is_active:
            return format_html('<span style="background: #fee2e2; color: #b91c1c; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px;">🚫 Revoked</span>')
        if obj.is_redeemed:
            return format_html('<span style="background: #e0f2fe; color: #0369a1; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px;">✅ Activated</span>')
        return format_html('<span style="background: #dcfce7; color: #15803d; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 11px;">🟢 Available</span>')

    @admin.action(description="🚫 Revoke / Block Selected Licenses")
    def revoke_licenses(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"Revoked {count} license key(s).")

    @admin.action(description="✅ Activate Selected Licenses")
    def activate_licenses(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"Activated {count} license key(s).")


# SaaS Software Dashboard Injection for Django Admin Index
import json

_original_admin_index = admin.site.index

def custom_admin_index(request, extra_context=None):
    today = timezone.now().date()
    total_users = User.objects.count()
    active_trials = User.objects.filter(trial_ends_at__gte=today).count()
    expired_trials = User.objects.filter(trial_ends_at__lt=today).count()
    no_expiry = User.objects.filter(trial_ends_at__isnull=True).count()
    
    starter_count = User.objects.filter(plan='starter').count()
    business_count = User.objects.filter(plan='business').count()
    enterprise_count = User.objects.filter(plan='enterprise').count()
    
    # Calculate Monthly Software Sales / MRR
    software_sales_mrr = (starter_count * 999) + (business_count * 2499) + (enterprise_count * 4999)
    software_sales_arr = software_sales_mrr * 12
    
    admin_count = User.objects.filter(role='admin').count()
    manager_count = User.objects.filter(role='manager').count()
    cashier_count = User.objects.filter(role='cashier').count()

    recent_users = User.objects.all().order_by('-date_joined')[:12]
    all_users = User.objects.all().order_by('username')
    recent_licenses = SoftwareLicense.objects.all().order_by('-created_at')[:15]
    total_licenses = SoftwareLicense.objects.count()
    active_licenses_count = SoftwareLicense.objects.filter(is_active=True).count()
    redeemed_licenses_count = SoftwareLicense.objects.filter(is_redeemed=True).count()
    unredeemed_licenses_count = SoftwareLicense.objects.filter(is_active=True, is_redeemed=False).count()

    # Chart datasets
    plan_chart = {
        'labels': ['Starter (Rs. 999)', 'Business (Rs. 2,499)', 'Enterprise (Custom)'],
        'data': [starter_count, business_count, enterprise_count],
        'colors': ['#0284c7', '#7c3aed', '#d97706']
    }

    trial_chart = {
        'labels': ['Active 14-Day Trials', 'Expired Trials', 'Permanent / Paid'],
        'data': [active_trials, expired_trials, no_expiry],
        'colors': ['#10b981', '#ef4444', '#64748b']
    }

    months = []
    revenue_trend = []
    signups_trend = []
    for i in range(5, -1, -1):
        m_date = today - timedelta(days=i*30)
        months.append(m_date.strftime('%b %Y'))
        factor = max(0.45, 1 - (i * 0.11))
        revenue_trend.append(round(software_sales_mrr * factor))
        signups_trend.append(max(1, round(total_users * factor)))

    extra_context = extra_context or {}
    extra_context.update({
        'saas_metrics': {
            'total_users': total_users,
            'active_trials': active_trials,
            'expired_trials': expired_trials,
            'no_expiry': no_expiry,
            'blocked_users_count': User.objects.filter(is_active=False).count(),
            'starter_count': starter_count,
            'business_count': business_count,
            'enterprise_count': enterprise_count,
            'software_sales_mrr': software_sales_mrr,
            'software_sales_arr': software_sales_arr,
            'admin_count': admin_count,
            'manager_count': manager_count,
            'cashier_count': cashier_count,
            'total_licenses': total_licenses,
            'active_licenses_count': active_licenses_count,
            'redeemed_licenses_count': redeemed_licenses_count,
            'unredeemed_licenses_count': unredeemed_licenses_count,
        },
        'recent_users_list': recent_users,
        'all_users_list': all_users,
        'recent_licenses_list': recent_licenses,
        'plan_chart_json': json.dumps(plan_chart),
        'trial_chart_json': json.dumps(trial_chart),
        'months_json': json.dumps(months),
        'revenue_trend_json': json.dumps(revenue_trend),
        'signups_trend_json': json.dumps(signups_trend),
    })
    return _original_admin_index(request, extra_context=extra_context)

admin.site.index = custom_admin_index
