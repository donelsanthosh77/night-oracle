"""The owner's staffing rule, written as code (it is in no file)."""
import math

from oracle import config


def staff_plan(guests: float) -> dict:
    """1 cook per 10 guests (max 3) + always 1 in service."""
    guests = max(0, min(config.SEATS, guests))
    cooks = min(config.MAX_COOKS, math.ceil(guests / config.GUESTS_PER_COOK))
    return {"kitchen": cooks, "service": config.SERVICE_STAFF,
            "total": cooks + config.SERVICE_STAFF}
