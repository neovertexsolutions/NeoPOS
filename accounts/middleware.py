from django.shortcuts import redirect


class SubscriptionAccessMiddleware:
    """Send expired users to payment proof submission before protected app pages."""

    ALLOWED_PREFIXES = (
        '/admin/',
        '/accounts/upgrade/',
        '/accounts/activate-license/',
        '/accounts/profile/',
        '/accounts/login/',
        '/accounts/register/',
        '/accounts/logout/',
        '/login/',
        '/register/',
        '/logout/',
        '/static/',
        '/media/',
        '/about/',
        '/pricing/',
        '/contact/',
        '/pos-showcase/',
        '/privacy-policy/',
        '/terms-of-service/',
        '/security/',
        '/hardware-support/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.has_active_access:
            if not request.path.startswith(self.ALLOWED_PREFIXES):
                return redirect('upgrade_request')
        return self.get_response(request)