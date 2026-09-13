REPS_SUBDOMAIN_PREFIX = "reps."


class SubdomainRoutingMiddleware:
    """Serves the sales rep portal at its own subdomain root (e.g.
    reps.learnritepublishers.com/login/) instead of under /reps/ on the main
    site - the client doesn't want it feeling bundled with the storefront.

    Swapping request.urlconf makes reps.urls the ENTIRE url space for that
    request, so it must run early enough that everything downstream
    (URL resolution, {% url %} tags in the reps templates) sees it. Requests
    to the main domain are untouched and keep working via the existing
    /reps/ path mounted in learnrite/urls.py."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0]
        if host.startswith(REPS_SUBDOMAIN_PREFIX):
            request.urlconf = "reps.subdomain_urls"
        return self.get_response(request)
