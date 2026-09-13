from store.logos import random_logo_path


def random_logo(request):
    """A fresh random logo color on every page load, storefront and reps
    portal alike (see templates/_nav.html and reps/base_reps.html) - the
    client wants genuine variety per page, not a fixed color per area."""
    return {"logo_path": random_logo_path()}
