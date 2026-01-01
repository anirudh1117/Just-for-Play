from market.models import Instrument
from market.constants import EXCHANGE_NSE, INSTRUMENT_EQ


# ---------------------------------------------------------
# Phase-1 Universe Selector
# ---------------------------------------------------------

EXCLUDE_PATTERNS = [
    "-BE",
    "-BL",
    "-BZ",
    "SME",
]


def _is_excluded(symbol: str) -> bool:
    symbol = symbol.upper()
    return any(pat in symbol for pat in EXCLUDE_PATTERNS)


def get_phase1_universe(limit=800):
    """
    Returns a queryset of tradable NSE EQ instruments.

    Phase-1 rules:
    - NSE EQ only
    - Exclude obvious illiquid categories
    - lot_size == 1
    - Hard limit on count
    """

    qs = Instrument.objects.filter(
        exchange=EXCHANGE_NSE,
        instrument_type=INSTRUMENT_EQ,
        lot_size=1,
    ).exclude(
        instrument_key__icontains="INE0"  # debt / bonds / PSU series
    ).only(
            "id", "instrument_key", "symbol"
    ).order_by("symbol")

    selected = []

    for inst in qs:
        if _is_excluded(inst.symbol):
            continue

        selected.append(inst)

        if len(selected) >= limit:
            break

    return selected
