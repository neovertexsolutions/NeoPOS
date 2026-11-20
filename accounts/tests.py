from django.test import TestCase
from django.urls import reverse

from .models import LicenseKeyOption, SoftwareLicense, User


class LicenseKeyTypeControlTests(TestCase):
    def setUp(self):
        self.superadmin = User.objects.create_superuser(
            username='superadmin',
            email='superadmin@example.com',
            password='test-password',
        )
        self.store_admin = User.objects.create_user(
            username='store-admin',
            password='test-password',
            role='admin',
        )

    def test_admin_dashboard_hides_license_type_controls_from_superadmin(self):
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse('admin:index'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'License Key Type Controls')
        self.assertNotContains(response, 'Software License Key Generator Module')
        self.assertNotContains(response, 'Generate License Key')
        self.assertContains(response, "document.addEventListener('DOMContentLoaded'")
        self.assertContains(response, 'revenueGrowthChart')
        self.assertNotContains(response, '// License Key Clipboard Copy Helper')

    def test_superadmin_can_disable_license_type(self):
        option = LicenseKeyOption.objects.get(plan='starter', duration='30')
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse('manage_license_key_option_action', args=[option.id]),
            {'action': 'disable'},
        )

        self.assertRedirects(response, '/admin/', fetch_redirect_response=False)
        option.refresh_from_db()
        self.assertFalse(option.is_enabled)

    def test_superadmin_license_type_form_passes_csrf_validation(self):
        client = self.client_class(enforce_csrf_checks=True)
        client.force_login(self.superadmin)

        dashboard = client.get('/admin/')
        option = LicenseKeyOption.objects.get(plan='starter', duration='30')

        self.assertEqual(dashboard.status_code, 200)
        self.assertIn('sahajpos_csrf_v2', client.cookies)
        response = client.post(
            reverse('manage_license_key_option_action', args=[option.id]),
            {
                'action': 'disable',
                'csrfmiddlewaretoken': client.cookies['sahajpos_csrf_v2'].value,
            },
            HTTP_REFERER='/admin/',
        )

        self.assertEqual(response.status_code, 302)
        option.refresh_from_db()
        self.assertFalse(option.is_enabled)

    def test_non_superadmin_cannot_change_license_type(self):
        option = LicenseKeyOption.objects.get(plan='starter', duration='30')
        self.client.force_login(self.store_admin)

        response = self.client.post(
            reverse('manage_license_key_option_action', args=[option.id]),
            {'action': 'disable'},
        )

        self.assertEqual(response.status_code, 403)
        option.refresh_from_db()
        self.assertTrue(option.is_enabled)

    def test_generator_rejects_disabled_license_type(self):
        LicenseKeyOption.objects.filter(plan='starter', duration='30').update(is_enabled=False)
        self.client.force_login(self.store_admin)

        response = self.client.post(
            reverse('generate_license_action'),
            {'plan': 'starter', 'duration': '30'},
        )

        self.assertRedirects(response, '/admin/', fetch_redirect_response=False)
        self.assertFalse(SoftwareLicense.objects.exists())

    def test_disabled_license_type_cannot_be_redeemed(self):
        LicenseKeyOption.objects.filter(plan='starter', duration='30').update(is_enabled=False)
        license_obj = SoftwareLicense.objects.create(
            license_key='SPOS-STR-1M-1234-5678-9ABC',
            plan='starter',
            duration='30',
        )
        self.client.force_login(self.store_admin)

        response = self.client.post(
            reverse('activate_license'),
            {'license_key': license_obj.license_key},
        )

        self.assertContains(response, 'license type is currently disabled')
        license_obj.refresh_from_db()
        self.assertFalse(license_obj.is_redeemed)

    def test_generator_allows_enabled_license_type(self):
        self.client.force_login(self.store_admin)

        response = self.client.post(
            reverse('generate_license_action'),
            {'plan': 'starter', 'duration': '30'},
        )

        self.assertRedirects(response, '/admin/', fetch_redirect_response=False)
        self.assertTrue(SoftwareLicense.objects.filter(plan='starter', duration='30').exists())
