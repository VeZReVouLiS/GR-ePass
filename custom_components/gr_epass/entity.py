"""Shared entity plumbing.

Kept here so every platform attaches to the same device; the identifiers must
stay byte-identical or Home Assistant creates duplicates.
"""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .operators import Operator


def account_device_info(account_id: str, operator: Operator) -> DeviceInfo:
    """Device that represents the subscription itself."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"account_{account_id}")},
        name=f"e-PASS {account_id}",
        manufacturer=operator.name,
        model="my e-PASS account",
        configuration_url=operator.portal_url,
    )
