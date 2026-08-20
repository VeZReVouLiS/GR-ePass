"""Sidebar panel registration for Attiki Odos e-Pass.

Home Assistant lets an integration serve its own frontend module and register it
as a panel, so the user gets a working screen straight after install without
building a dashboard or editing YAML.

The panel is registered once per Home Assistant instance, not once per config
entry: the module discovers every subscription itself, and registering the same
frontend_url_path twice raises.
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PANEL_FILE = "attiki-odos-epass-panel.js"
PANEL_COMPONENT = "attiki-odos-epass-panel"
PANEL_URL = f"/{DOMAIN}-panel/{PANEL_FILE}"
PANEL_TITLE = "e-PASS"
PANEL_ICON = "mdi:boom-gate-arrow-up"

_REGISTERED = f"{DOMAIN}_panel_registered"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Serve the module and add the sidebar entry."""
    if hass.data.get(_REGISTERED):
        return

    source = Path(__file__).parent / "panel" / PANEL_FILE
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                PANEL_URL,
                str(source),
                # The file ships with the integration, so it changes on upgrade
                # and must not be cached across versions.
                cache_headers=False,
            )
        ]
    )

    # The module url carries a cache-busting token. Without it a caching proxy
    # in front of Home Assistant -- Cloudflare Tunnel, nginx, anything that adds
    # max-age to static files -- keeps serving the previous panel after an
    # upgrade, and the user sees an old UI with no way to know why.
    #
    # The token mixes the version with the file's own size and mtime, so it also
    # changes for a reinstall that keeps the version number and for anyone
    # editing the file in place. Both stats are read in the executor because
    # this runs on the event loop.
    integration = await async_get_integration(hass, DOMAIN)
    stat = await hass.async_add_executor_job(source.stat)
    token = f"{integration.version or 'dev'}-{stat.st_size:x}-{int(stat.st_mtime):x}"
    module_url = f"{PANEL_URL}?v={token}"

    await panel_custom.async_register_panel(
        hass,
        webcomponent_name=PANEL_COMPONENT,
        frontend_url_path=DOMAIN,
        module_url=module_url,
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        # The panel exposes the balance and can prepare a top-up, so it sits
        # behind admin like the rest of the billing surface.
        require_admin=True,
        config={},
        config_panel_domain=DOMAIN,
    )
    hass.data[_REGISTERED] = True
    _LOGGER.debug("Registered the e-PASS panel at /%s from %s", DOMAIN, module_url)


def async_unregister_panel(hass: HomeAssistant) -> None:
    """Drop the sidebar entry when the last entry unloads."""
    if not hass.data.pop(_REGISTERED, False):
        return
    frontend.async_remove_panel(hass, DOMAIN)
    _LOGGER.debug("Removed the e-PASS panel")
