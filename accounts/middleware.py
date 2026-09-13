from django.shortcuts import redirect
from django.urls import Resolver404, resolve

from accounts.models import Profile

EXEMPT_URL_NAMES = {
    "account_setup", "logout",
    "verify_email", "verify_email_pending", "resend_verification_email",
}
EXEMPT_PATH_PREFIXES = ("/admin/", "/static/", "/media/", "/auth/", "/reps/")


class RequireAccountSetupMiddleware:
    """Send an authenticated customer through two gates before anything
    else: verifying their email, then confirming account type/location/
    phone/address (e.g. a fresh Google sign-up, which never goes through
    RegisterForm) - since every price and every checkout on the site
    depends on that profile being real."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        # The reps subdomain runs its own urlconf at the request's own path
        # root (e.g. "/login/") - checked directly rather than via path
        # prefix, since request.urlconf doesn't affect resolve()/get_urlconf()
        # until later in the request cycle, so a plain path-prefix check
        # would see "/login/" and wrongly treat it as a customer route.
        on_reps_subdomain = getattr(request, "urlconf", None) == "reps.subdomain_urls"
        if (
            not on_reps_subdomain
            and user.is_authenticated
            and not user.is_staff
            and not request.path.startswith(EXEMPT_PATH_PREFIXES)
        ):
            try:
                url_name = resolve(request.path).url_name
            except Resolver404:
                url_name = None
            if url_name not in EXEMPT_URL_NAMES:
                profile, _ = Profile.objects.get_or_create(user=user)
                if not profile.is_verified:
                    return redirect("verify_email_pending")
                if not profile.profile_confirmed:
                    return redirect("account_setup")
        return self.get_response(request)
