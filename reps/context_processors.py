def rep_branding(request):
    """Gives the sales rep portal its own logo colour so it reads as a
    distinct area from the customer storefront at a glance - see
    templates/_nav.html, which falls back to the default logo everywhere
    else."""
    if request.path.startswith("/reps/"):
        return {"logo_path": "store/logo_green.svg"}
    return {}
