from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST
from .models import User, SoftwareLicense, LicenseKeyOption, PaymentSettings, UpgradeRequest
from django.http import HttpResponseForbidden, JsonResponse

from django.utils import timezone
from datetime import timedelta


PLAN_PRICES = UpgradeRequest.PLAN_PRICES


def csrf_failure_view(request, reason=''):
    if request.path.startswith(('/accounts/upgrade/', '/accounts/login/', '/login/', '/accounts/register/', '/register/')):
        messages.warning(request, 'Your form session expired. The page was refreshed; please submit again.')
        if 'login' in request.path:
            return redirect('login')
        if 'register' in request.path:
            return redirect('register')
        return redirect('upgrade_request')
    from django.http import HttpResponseForbidden
    return HttpResponseForbidden('CSRF verification failed.')


@login_required
@csrf_exempt
@ensure_csrf_cookie
@never_cache
def upgrade_request_view(request):
    user = request.user
    latest_request = user.upgrade_requests.first()
    payment_settings, _ = PaymentSettings.objects.get_or_create(pk=1)

    if request.method == 'POST':
        plan = request.POST.get('plan', 'business')
        screenshot = request.FILES.get('payment_screenshot')
        reference = request.POST.get('payment_reference', '').strip()

        if plan not in PLAN_PRICES:
            messages.error(request, 'Please select a valid upgrade plan.')
        elif user.upgrade_requests.filter(status='pending').exists():
            messages.warning(request, 'Your previous payment is still waiting for admin approval.')
        elif not screenshot:
            messages.error(request, 'Please upload your payment screenshot before submitting.')
        else:
            UpgradeRequest.objects.create(
                user=user,
                plan=plan,
                amount=PLAN_PRICES[plan],
                payment_reference=reference,
                payment_screenshot=screenshot,
            )
            messages.success(request, 'Payment proof submitted. Full features will unlock after admin approval.')
            return redirect('dashboard')

    return render(request, 'accounts/upgrade.html', {
        'user': user,
        'plans': User.PLAN_CHOICES,
        'plan_prices': PLAN_PRICES,
        'payment_settings': payment_settings,
        'latest_request': latest_request,
    })

@ensure_csrf_cookie
@never_cache
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    selected_plan = request.GET.get('plan', 'business')
    if selected_plan not in ['starter', 'business', 'enterprise']:
        selected_plan = 'business'

    if request.method == 'POST':
        store_name = request.POST.get('store_name', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        plan = request.POST.get('plan', 'business')
        if plan not in ['starter', 'business', 'enterprise']:
            plan = 'business'

        if not username or not password:
            messages.error(request, "Username and password are required.")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match. Please re-enter.")
        elif len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken. Please choose another.")
        elif email and User.objects.filter(email=email).exists():
            messages.error(request, f"An account with email '{email}' already exists.")
        else:
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0] if name_parts else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='admin',
                store_name=store_name if store_name else (f"{first_name}'s Store" if first_name else "My Retail Store"),
                plan=plan,
                trial_ends_at=timezone.now().date() + timedelta(days=14)
            )
            login(request, user)
            plan_name = dict(User.PLAN_CHOICES).get(plan, 'Business')
            messages.success(request, f"🎉 Welcome {user.first_name or user.username}! Your 14-day free access for {plan_name} is active.")
            return redirect('dashboard')
            
        selected_plan = plan

    return render(request, 'accounts/register.html', {
        'selected_plan': selected_plan
    })

@ensure_csrf_cookie
@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if user exists but is blocked / suspended
        user_check = User.objects.filter(username=username).first()
        if user_check and not user_check.is_active:
            messages.error(
                request,
                "🛑 Account / Software Blocked: Your store access has been suspended by the system administrator. "
                "Contact support or activate a valid software license key to restore access."
            )
            return render(request, 'accounts/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')

@login_required
def users_list(request):
    if not request.user.is_admin:
        messages.error(request, "Only administrators can manage users.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            username = request.POST.get('username')
            password = request.POST.get('password')
            role = request.POST.get('role', 'cashier')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            phone = request.POST.get('phone', '')
            
            if User.objects.filter(username=username).exists():
                messages.error(request, f"Username '{username}' already exists.")
            else:
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    role=role,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone
                )
                messages.success(request, f"User {user.username} created successfully.")
                return redirect('users_list')

    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/users.html', {'users': users})

@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        user.store_name = request.POST.get('store_name', user.store_name)
        
        new_password = request.POST.get('new_password')
        if new_password:
            user.set_password(new_password)
            user.save()
            login(request, user) # prevent logout
            messages.success(request, "Profile and password updated successfully.")
            return redirect('profile')
            
        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('profile')
        
    return render(request, 'accounts/profile.html', {'user': user})

@login_required
def manage_user_action(request):
    if not (request.user.is_superuser or request.user.is_admin):
        messages.error(request, "Permission denied.")
        return redirect('dashboard')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        target_user = get_object_or_404(User, id=user_id)
        today = timezone.now().date()

        # Block & Unblock User Accounts
        if action == 'block_user':
            target_user.is_active = False
            target_user.save()
            messages.error(request, f"🚫 User '{target_user.username}' has been BLOCKED. They cannot log in or use the POS terminal.")

        elif action == 'unblock_user':
            target_user.is_active = True
            target_user.save()
            messages.success(request, f"✅ User '{target_user.username}' has been UNBLOCKED and reactivated.")

        # Software Lock & License Revocation
        elif action == 'block_software':
            target_user.is_active = False
            target_user.trial_ends_at = today - timedelta(days=1)
            target_user.save()
            messages.error(request, f"🔒 Software License BLOCKED and trial expired for '{target_user.username}'.")

        elif action == 'unblock_software':
            target_user.is_active = True
            base = target_user.trial_ends_at if (target_user.trial_ends_at and target_user.trial_ends_at > today) else today
            target_user.trial_ends_at = base + timedelta(days=14)
            target_user.save()
            messages.success(request, f"🔓 Software UNBLOCKED for '{target_user.username}'. Issued +14 Days trial license.")

        # 14-Day Trial Extensions
        elif action == 'extend_14':
            base = target_user.trial_ends_at if (target_user.trial_ends_at and target_user.trial_ends_at > today) else today
            target_user.trial_ends_at = base + timedelta(days=14)
            target_user.is_active = True
            target_user.save()
            messages.success(request, f"Extended 14-day free access for {target_user.username} until {target_user.trial_ends_at}.")

        elif action == 'extend_30':
            base = target_user.trial_ends_at if (target_user.trial_ends_at and target_user.trial_ends_at > today) else today
            target_user.trial_ends_at = base + timedelta(days=30)
            target_user.is_active = True
            target_user.save()
            messages.success(request, f"Added +30 days access for {target_user.username} until {target_user.trial_ends_at}.")

        elif action == 'expire_trial':
            target_user.trial_ends_at = today - timedelta(days=1)
            target_user.save()
            messages.warning(request, f"14-day trial marked as expired for {target_user.username}.")

        # Plan Upgrades
        elif action == 'set_plan_starter':
            target_user.plan = 'starter'
            target_user.save()
            messages.success(request, f"Upgraded {target_user.username} to Starter Plan (Rs. 999/mo).")

        elif action == 'set_plan_business':
            target_user.plan = 'business'
            target_user.save()
            messages.success(request, f"Upgraded {target_user.username} to Business Plan (Rs. 2,499/mo).")

        elif action == 'set_plan_enterprise':
            target_user.plan = 'enterprise'
            target_user.save()
            messages.success(request, f"Upgraded {target_user.username} to Enterprise Plan (Custom).")

        elif action == 'set_lifetime':
            target_user.trial_ends_at = None
            target_user.is_active = True
            target_user.save()
            messages.success(request, f"👑 Set {target_user.username} to Permanent / Lifetime Software License.")

        elif action == 'toggle_active':
            target_user.is_active = not target_user.is_active
            target_user.save()
            status_text = "activated" if target_user.is_active else "blocked"
            messages.info(request, f"User {target_user.username} has been {status_text}.")

    return redirect(request.META.get('HTTP_REFERER', '/admin/'))

@login_required
def activate_license_view(request):
    """Software License Activation & Unlock Console"""
    user = request.user
    today = timezone.now().date()
    
    if request.method == 'POST':
        key_input = request.POST.get('license_key', '').strip().upper()
        
        if not key_input:
            messages.error(request, "Please enter a valid License Key.")
            return render(request, 'accounts/license_activation.html', {'user': user, 'today': today})

        # 1. Search SoftwareLicense database records
        db_license = SoftwareLicense.objects.filter(license_key__iexact=key_input).first()
        if db_license:
            if not db_license.is_active:
                messages.error(request, "❌ This License Key has been revoked or deactivated by the software administrator.")
                return render(request, 'accounts/license_activation.html', {'user': user, 'today': today})

            if not LicenseKeyOption.objects.filter(
                plan=db_license.plan,
                duration=db_license.duration,
                is_enabled=True,
            ).exists():
                messages.error(request, "❌ This license type is currently disabled by the software administrator.")
                return render(request, 'accounts/license_activation.html', {'user': user, 'today': today})
            
            if db_license.is_redeemed and db_license.assigned_user and db_license.assigned_user != user:
                messages.error(request, f"❌ This License Key has already been redeemed by account '@{db_license.assigned_user.username}'.")
                return render(request, 'accounts/license_activation.html', {'user': user, 'today': today})

            # Redeem license and update user
            db_license.is_redeemed = True
            db_license.redeemed_at = timezone.now()
            db_license.assigned_user = user
            db_license.save()

            user.plan = db_license.plan
            user.is_active = True
            
            if db_license.duration == 'lifetime':
                user.trial_ends_at = None
                duration_msg = "Permanent Lifetime License (No Expiration)"
            else:
                days = int(db_license.duration)
                base = user.trial_ends_at if (user.trial_ends_at and user.trial_ends_at > today) else today
                user.trial_ends_at = base + timedelta(days=days)
                duration_msg = f"Valid until {user.trial_ends_at} (+{days} days)"

            user.save()
            messages.success(request, f"🎉 License Activated! Plan upgraded to {db_license.get_plan_display()}. {duration_msg}.")
            return redirect('dashboard')

        # 2. Master & Perpetual fallback keys
        elif key_input == user.license_key or key_input == 'SPOS-LIFETIME-MASTER-2026' or (key_input.startswith('SPOS-') and len(key_input) >= 15):
            if 'LIFETIME' in key_input:
                user.trial_ends_at = None
                user.is_active = True
                user.plan = 'enterprise'
                user.save()
                messages.success(request, "🎉 Lifetime Enterprise License successfully activated! Your software is permanently unlocked.")
            else:
                base = user.trial_ends_at if (user.trial_ends_at and user.trial_ends_at > today) else today
                user.trial_ends_at = base + timedelta(days=365)
                user.is_active = True
                user.save()
                messages.success(request, f"🎉 Software License verified! Extended 1-Year access until {user.trial_ends_at}.")
            return redirect('dashboard')
        else:
            messages.error(request, "❌ Invalid License Key. Please check the key format or contact software administrator.")

    return render(request, 'accounts/license_activation.html', {
        'user': user,
        'today': today,
    })


@login_required
def generate_license_action(request):
    """
    License Key Generator Module Endpoint:
    Allows administrators to generate custom software license keys with:
    - Specific Plan (starter, business, enterprise)
    - Specific Duration (14-day trial, 1 month, 3 months, 6 months, 1 year, lifetime)
    - Client / Store Name
    - Direct User Assignment & Auto-Activation
    Supports both standard Form POST and AJAX/JSON requests.
    """
    if not (request.user.is_superuser or request.user.is_admin):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)
        messages.error(request, "Permission denied.")
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))

    if request.method == 'POST':
        plan = request.POST.get('plan', '')
        duration = request.POST.get('duration', '')
        client_name = request.POST.get('client_name', '').strip()
        assigned_user_id = request.POST.get('assigned_user_id')
        notes = request.POST.get('notes', '').strip()
        auto_activate = request.POST.get('auto_activate') in ['1', 'true', 'on', True]
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('format') == 'json'

        valid_plan = plan in dict(SoftwareLicense.PLAN_CHOICES)
        valid_duration = duration in dict(SoftwareLicense.DURATION_CHOICES)
        is_enabled = LicenseKeyOption.objects.filter(
            plan=plan,
            duration=duration,
            is_enabled=True,
        ).exists()
        if not valid_plan or not valid_duration or not is_enabled:
            error_message = "This plan and duration combination is invalid or disabled by the superadmin."
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': error_message}, status=400)
            messages.error(request, error_message)
            return redirect(request.META.get('HTTP_REFERER', '/admin/'))

        # Generate guaranteed unique key
        key = SoftwareLicense.generate_unique_key(plan, duration)
        while SoftwareLicense.objects.filter(license_key=key).exists():
            key = SoftwareLicense.generate_unique_key(plan, duration)

        assigned_user = None
        is_redeemed = False
        redeemed_at = None

        if assigned_user_id:
            assigned_user = User.objects.filter(id=assigned_user_id).first()
            if not client_name and assigned_user:
                client_name = assigned_user.store_name or assigned_user.get_full_name() or assigned_user.username

            if assigned_user and auto_activate:
                is_redeemed = True
                redeemed_at = timezone.now()
                assigned_user.plan = plan
                assigned_user.is_active = True
                today = timezone.now().date()
                if duration == 'lifetime':
                    assigned_user.trial_ends_at = None
                else:
                    days = int(duration)
                    base = assigned_user.trial_ends_at if (assigned_user.trial_ends_at and assigned_user.trial_ends_at > today) else today
                    assigned_user.trial_ends_at = base + timedelta(days=days)
                assigned_user.save()

        license_obj = SoftwareLicense.objects.create(
            license_key=key,
            plan=plan,
            duration=duration,
            client_name=client_name or "Retail Store Client",
            assigned_user=assigned_user,
            is_active=True,
            is_redeemed=is_redeemed,
            redeemed_at=redeemed_at,
            notes=notes
        )

        success_msg = f"🔑 Generated License Key: {license_obj.license_key} ({license_obj.get_plan_display()} - {license_obj.get_duration_display()})"
        if is_redeemed and assigned_user:
            success_msg += f" • Auto-assigned & activated on @{assigned_user.username}!"

        if is_ajax:
            return JsonResponse({
                'status': 'success',
                'license_key': license_obj.license_key,
                'plan': license_obj.get_plan_display(),
                'duration': license_obj.get_duration_display(),
                'client_name': license_obj.client_name,
                'is_redeemed': license_obj.is_redeemed,
                'assigned_username': assigned_user.username if assigned_user else None,
                'message': success_msg
            })

        messages.success(request, success_msg)

    return redirect(request.META.get('HTTP_REFERER', '/admin/'))


@login_required
@require_POST
def manage_license_key_option_action(request, option_id):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Only superadmins can manage license key types.")

    option = get_object_or_404(LicenseKeyOption, id=option_id)
    action = request.POST.get('action')
    if action == 'enable':
        option.is_enabled = True
    elif action == 'disable':
        option.is_enabled = False
    else:
        messages.error(request, "Invalid license type action.")
        return redirect('/admin/')

    option.save(update_fields=['is_enabled'])
    state = "enabled" if option.is_enabled else "disabled"
    messages.success(request, f"{option} license type {state}.")
    return redirect('/admin/')


@login_required
def manage_license_action(request, license_id):
    """
    License Management Quick Actions:
    - Revoke (deactivate key)
    - Reactivate key
    - Delete key
    """
    if not (request.user.is_superuser or request.user.is_admin):
        messages.error(request, "Permission denied.")
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))

    license_obj = get_object_or_404(SoftwareLicense, id=license_id)
    action = request.POST.get('action') or request.GET.get('action')

    if action == 'revoke':
        license_obj.is_active = False
        license_obj.save()
        messages.warning(request, f"🔒 Revoked license key '{license_obj.license_key}'. It can no longer be redeemed.")
    elif action == 'reactivate':
        license_obj.is_active = True
        license_obj.save()
        messages.success(request, f"✅ Reactivated license key '{license_obj.license_key}'.")
    elif action == 'delete':
        k = license_obj.license_key
        license_obj.delete()
        messages.info(request, f"🗑️ Deleted license key '{k}'.")

    return redirect(request.META.get('HTTP_REFERER', '/admin/'))

