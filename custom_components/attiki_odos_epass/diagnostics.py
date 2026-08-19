"""Diagnostics support for Attiki Odos e-PASS."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from . import EpassConfigEntry

TO_REDACT = {
    CONF_PASSWORD,
    CONF_USERNAME,
    "AltEmail",
    "AlternatePhone",
    "BankAccountNumber",
    "BankTransitNumber",
    "BillingAddress",
    "Email",
    "Fax",
    "FirstName",
    "LastName",
    "MailingAddress",
    "MobilePhone",
    "NationalInsNumber",
    "Password",
    "PaymentNumber",
    "PlateNum",
    "PreAuthCardHolder",
    "PreAuthCardNumber",
    "PrimaryPhone",
    "Sms",
    "TaxFiscalId",
    "UserLogonId",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: EpassConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    data = coordinator.data
    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "account": async_redact_data(data.account, TO_REDACT),
        "transponders": [
            async_redact_data(transponder, TO_REDACT)
            for transponder in data.transponders
        ],
        "stats": {
            key: {period: asdict(stats) for period, stats in periods.items()}
            for key, periods in data.stats.items()
        },
        "last_pass": {
            key: async_redact_data(dict(value), TO_REDACT)
            for key, value in data.last_pass.items()
        },
    }
