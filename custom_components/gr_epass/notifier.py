"""Send a prepared payment link to wherever the user reads notifications.

Deliberately built on ``notify.send_message`` and a notify entity rather than on
one messenger: the link is just text, and every install has a different way of
receiving text. Nothing here knows about Telegram.

The link is not secret in the way a password is, but it is worth being clear
about what is being sent: a single-use URL that expires in ten minutes, with the
amount and card already fixed in the signature. The worst a leaked one can do is
top up the owner's own toll balance.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_NOTIFY_TARGET

_LOGGER = logging.getLogger(__name__)

TEXT = {
    "el": {
        "title": "GR e-Pass — ανανέωση υπολοίπου",
        "body": (
            "Ποσό: {amount}\n"
            "Κάρτα: {card}\n"
            "Ο σύνδεσμος λήγει σε {minutes} λεπτά και ισχύει για μία χρήση.\n\n"
            "{link}"
        ),
        "no_link": "Δεν υπάρχει ενεργός σύνδεσμος πληρωμής.",
        "no_target": (
            "Δεν έχει οριστεί πού να σταλεί. Ρυθμίσεις → Devices & Services → "
            "GR e-Pass → Configure."
        ),
    },
    "en": {
        "title": "GR e-Pass — top up",
        "body": (
            "Amount: {amount}\n"
            "Card: {card}\n"
            "The link expires in {minutes} minutes and works once.\n\n"
            "{link}"
        ),
        "no_link": "There is no active payment link.",
        "no_target": (
            "No destination is set. Settings → Devices & Services → GR e-Pass → "
            "Configure."
        ),
    },
}


def _text(hass: HomeAssistant) -> dict[str, str]:
    return TEXT["el"] if (hass.config.language or "").startswith("el") else TEXT["en"]


def configured_target(entry: Any) -> str | None:
    """The notify entity the user picked, if any."""
    target = entry.options.get(CONF_NOTIFY_TARGET)
    return target or None


async def async_send_link(
    hass: HomeAssistant,
    entry: Any,
    coordinator: Any,
    target: str | None = None,
) -> str:
    """Send the current payment link. Returns the entity it went to.

    Raises ``HomeAssistantError`` when there is nothing to send or nowhere to
    send it, so both the service and the page report the same thing.
    """
    words = _text(hass)
    destination = target or configured_target(entry)
    if not destination:
        raise HomeAssistantError(words["no_target"])

    button = coordinator.topup_button
    link = getattr(button, "link", None) if button else None
    if not link:
        raise HomeAssistantError(words["no_link"])

    await hass.services.async_call(
        "notify",
        "send_message",
        {
            "entity_id": destination,
            "title": words["title"],
            "message": words["body"].format(
                amount=button.amount_text,
                card=button.card_text,
                minutes=button.minutes_left,
                link=link,
            ),
        },
        blocking=True,
    )
    _LOGGER.debug("Payment link sent to %s", destination)
    return destination
