"""Shared entity plumbing for Attiki Odos e-Pass."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

BRAND = "Αττική Οδός"


def account_device_info(account_id: str) -> DeviceInfo:
    """Device that represents the subscription itself.

    Kept here so every platform attaches to the same device; the identifiers
    must stay byte-identical or Home Assistant creates duplicates.
    """
    return DeviceInfo(
        identifiers={(DOMAIN, f"account_{account_id}")},
        name=f"e-PASS {account_id}",
        manufacturer=BRAND,
        model="my e-PASS account",
        configuration_url="https://epass.naodos.gr/",
    )
