"""Services for GR e-Pass.

``get_receipt`` fetches the operator's receipt for one payment order. It exists
because the bank sends the payer back to the portal's own receipt page, which
needs a portal login the Home Assistant browser tab does not have -- but the
same receipt is available over the API with the token the integration already
holds, keyed only by the order id.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .notifier import async_send_link

_LOGGER = logging.getLogger(__name__)

SERVICE_GET_RECEIPT = "get_receipt"
SERVICE_SEND_LINK = "send_link"

ATTR_ORDER_ID = "order_id"
ATTR_ENTRY_ID = "entry_id"
ATTR_WAIT = "wait"

# The bank confirms out of band, so a receipt asked for straight after payment is
# not there yet. The portal's own page retries once a second for thirty seconds;
# the same ceiling is used here.
_RETRY_DELAY = 1.0
_MAX_WAIT = 30

_NOT_FOUND = "API_WARN_TRANSACTION_NOT_FOUND"

ATTR_TARGET = "target"

SEND_LINK_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_TARGET): cv.entity_id,
        vol.Optional(ATTR_ENTRY_ID): cv.string,
    }
)

GET_RECEIPT_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ORDER_ID): cv.string,
        vol.Optional(ATTR_ENTRY_ID): cv.string,
        vol.Optional(ATTR_WAIT, default=False): cv.boolean,
    }
)


def _coordinator(hass: HomeAssistant, entry_id: str | None) -> Any:
    """Pick the subscription to ask. Only ambiguous with several set up."""
    entries = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    ]
    if not entries:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="no_loaded_entry"
        )
    if entry_id is not None:
        for entry in entries:
            if entry.entry_id == entry_id:
                return entry.runtime_data
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unknown_entry",
            translation_placeholders={"entry_id": entry_id},
        )
    if len(entries) > 1:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="entry_id_required"
        )
    return entries[0].runtime_data


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Register the integration's services once per instance."""
    if hass.services.has_service(DOMAIN, SERVICE_GET_RECEIPT):
        return

    async def async_get_receipt(call: ServiceCall) -> ServiceResponse:
        coordinator = _coordinator(hass, call.data.get(ATTR_ENTRY_ID))
        order_id = call.data.get(ATTR_ORDER_ID)
        if order_id is None:
            # Default to the last order handed to the bank, which is the one a
            # caller almost always means and the only one they have not had to
            # write down themselves.
            manager = coordinator.payment
            order_id = manager.last_handoff if manager is not None else None
        if not order_id:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="no_order_id"
            )
        attempts = _MAX_WAIT if call.data[ATTR_WAIT] else 1

        for attempt in range(1, attempts + 1):
            try:
                receipt = await coordinator.client.async_get_txn_receipt(order_id)
            except Exception as err:  # noqa: BLE001 - surfaced to the caller
                raise HomeAssistantError(
                    f"Could not fetch the receipt for order {order_id}: {err}"
                ) from err

            if receipt.get("Message") != _NOT_FOUND:
                return {"order_id": order_id, "found": True, "receipt": receipt}

            if attempt < attempts:
                await asyncio.sleep(_RETRY_DELAY)

        _LOGGER.debug(
            "No receipt for order %s after %s attempt(s)", order_id, attempts
        )
        return {"order_id": order_id, "found": False, "receipt": None}

    async def async_send_link_service(call: ServiceCall) -> None:
        entry_id = call.data.get(ATTR_ENTRY_ID)
        coordinator = _coordinator(hass, entry_id)
        entry = coordinator.config_entry
        await async_send_link(
            hass, entry, coordinator, call.data.get(ATTR_TARGET)
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_LINK,
        async_send_link_service,
        schema=SEND_LINK_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_RECEIPT,
        async_get_receipt,
        schema=GET_RECEIPT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


@callback
def async_unregister_services(hass: HomeAssistant) -> None:
    """Drop the services when the last entry goes."""
    hass.services.async_remove(DOMAIN, SERVICE_GET_RECEIPT)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_LINK)
