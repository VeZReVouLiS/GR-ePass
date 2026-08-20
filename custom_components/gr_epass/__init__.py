"""The Attiki Odos e-PASS integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import EpassClient
from .const import CONF_OPERATOR, DOMAIN
from .operators import get_operator
from .coordinator import EpassCoordinator
from .panel import async_register_panel, async_unregister_panel
from .payment import EpassPaymentManager, EpassPaymentView
from .services import async_register_services, async_unregister_services

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
    operator = get_operator(entry.data.get(CONF_OPERATOR))
    client = EpassClient(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        operator.base_url,
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

    await async_register_panel(hass)
    async_register_services(hass)

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EpassConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    # The panel is instance-wide, so it only goes when the last entry does.
    if unloaded and len(hass.config_entries.async_entries(DOMAIN)) <= 1:
        async_unregister_panel(hass)
        async_unregister_services(hass)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: EpassConfigEntry) -> None:
    """Reload when the user changes options (transponder selection, interval)."""
    await hass.config_entries.async_reload(entry.entry_id)
