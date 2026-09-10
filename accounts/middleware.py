from django.shortcuts import redirect
from django.urls import Resolver404, resolve

from accounts.models import Profile

EXEMPT_URL_NAMES = {"account_setup", "logout"}
EXEMPT_PATH_PREFIXES = ("/admin/", "/static/", "/media/", "/auth/")


class RequireAccountSetupMiddleware:
    """Send an authenticated customer with an unconfirmed Profile (e.g. a
    fresh Google sign-up, which never goes through RegisterForm) to the
    account type/location confirmation step before anything else, since
    every price on the site is looked up from that profile."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if (
            user.is_authenticated
            and not user.is_staff
            and not request.path.startswith(EXEMPT_PATH_PREFIXES)
        ):
            try:
                url_name = resolve(request.path).url_name
            except Resolver404:
                url_name = None
            if url_name not in EXEMPT_URL_NAMES:
                profile, _ = Profile.objects.get_or_create(user=user)
                if not profile.profile_confirmed:
                    return redirect("account_setup")
        return self.get_response(request)
