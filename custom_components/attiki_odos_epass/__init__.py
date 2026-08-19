"""The Attiki Odos e-PASS integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import EpassClient
from .const import DOMAIN
from .coordinator import EpassCoordinator
from .payment import EpassPaymentManager, EpassPaymentView

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
]

type EpassConfigEntry = ConfigEntry[EpassCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: EpassConfigEntry) -> bool:
    """Set up Attiki Odos e-PASS from a config entry."""
    # A dedicated session with a cookie jar, because the backend sits behind a
    # load balancer that pins sessions with cookies.
    session = async_create_clientsession(hass)
    client = EpassClient(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    coordinator = EpassCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    # One payment manager per Home Assistant instance, shared by every config
    # entry, because a single HTTP view serves them all: an order is found by
    # its nonce, so the manager must hold orders from every account.
    store = hass.data.setdefault(DOMAIN, {})
    if "payment" not in store:
        store["payment"] = EpassPaymentManager(hass)
        hass.http.register_view(EpassPaymentView(store["payment"]))
    coordinator.payment = store["payment"]

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EpassConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: EpassConfigEntry) -> None:
    """Reload when the user changes options (transponder selection, interval)."""
    await hass.config_entries.async_reload(entry.entry_id)
