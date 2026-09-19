from decimal import Decimal

# Client's commission table, keyed by total book quantity on the invoice -
# a rep's cut scales with how many books they move in one sale.
COMMISSION_TIERS = (
    (1, 40, Decimal("5.7")),
    (41, 80, Decimal("6.65")),
    (81, 250, Decimal("7.6")),
    (251, None, Decimal("9.5")),
)


def commission_rate_for_quantity(total_quantity):
    """The commission percentage for a given total book quantity, or 0 if
    there's nothing to sell yet (quantity <= 0)."""
    for low, high, rate in COMMISSION_TIERS:
        if total_quantity >= low and (high is None or total_quantity <= high):
            return rate
    return Decimal("0")
