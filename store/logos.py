import random

# The colored badge variants pulled from the logo artwork itself (see
# static/store/logo*.svg) - mint is the original/default and excluded here
# since the client wants genuine variety on every page load, not the
# original color turning up as one of several "random" options.
LOGO_VARIANTS = [
    "store/logo_purple.svg",
    "store/logo_yellow.svg",
    "store/logo_orange.svg",
    "store/logo_red.svg",
    "store/logo_green.svg",
]

# Same artwork, wordmark recolored white instead of black - the storefront
# variants above are made for a white navbar, but the admin sidebar/header
# is dark, so the black text was unreadable there.
ADMIN_LOGO_VARIANTS = [
    "admin/logo/logo_purple.svg",
    "admin/logo/logo_yellow.svg",
    "admin/logo/logo_orange.svg",
    "admin/logo/logo_red.svg",
    "admin/logo/logo_green.svg",
]


def random_logo_path():
    return random.choice(LOGO_VARIANTS)


def random_admin_logo_path():
    return random.choice(ADMIN_LOGO_VARIANTS)
