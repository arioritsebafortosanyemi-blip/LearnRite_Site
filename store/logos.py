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


def random_logo_path():
    return random.choice(LOGO_VARIANTS)
