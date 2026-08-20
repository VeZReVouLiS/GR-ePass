"""Stored-card picker for GR e-PASS.

A top-up reuses a card that the bank has already tokenised. There is no way to
add a card from here: SaveStoredCard only stores an alias, and the token itself
is minted by the bank during a real payment on their hosted page. So the first
charge always has to happen on epass.naodos.gr -- after that the card shows up
here and can be picked.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EpassConfigEntry
from .coordinator import EpassCoordinator
from .entity import account_device_info

_LOGGER = logging.getLogger(__name__)

NO_CARDS = "—"

BRAND_LABELS = {
    "visa": "Visa",
    "mastercard": "Mastercard",
    "maestro": "Maestro",
    "amex": "American Express",
    "diners": "Diners",
    "other": "Κάρτα",
}


def card_label(card: dict[str, Any]) -> str:
    """Human label for a stored card, close to how the portal shows it.

    The alias wins when the subscriber set one, because that is what they will
    recognise; otherwise fall back to brand plus the last four digits.
    """
    brand = BRAND_LABELS.get(card["brand"], BRAND_LABELS["other"])
    last_four = card.get("last_four") or "????"
    if card.get("alias"):
        return f"{card['alias']} ({brand} ••••{last_four})"
    return f"{brand} ••••{last_four}"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EpassConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the card picker."""
    coordinator = entry.runtime_data
    async_add_entities([EpassCardSelect(coordinator, str(coordinator.account_id))])


class EpassCardSelect(
    CoordinatorEntity[EpassCoordinator], SelectEntity, RestoreEntity
):
    """Which stored card a top-up should reuse."""

    _attr_has_entity_name = True
    _attr_translation_key = "payment_card"
    _attr_icon = "mdi:credit-card-outline"

    def __init__(self, coordinator: EpassCoordinator, account_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{account_id}_payment_card"
        self._attr_device_info = account_device_info(account_id, coordinator.operator)
        self._selected: str | None = None

    async def async_added_to_hass(self) -> None:
        """Restore the previous choice.

        A select does not persist its state on its own, and re-picking the card
        after every restart would be tedious.
        """
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) and last.state in self.options:
            self._selected = last.state
        self._sync_selection()
        self.coordinator.card_select = self

    @property
    def options(self) -> list[str]:
        cards = self.coordinator.data.payable_cards
        if not cards:
            return [NO_CARDS]
        return [card_label(card) for card in cards]

    @property
    def current_option(self) -> str | None:
        return self._selected

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        card = self.selected_card
        return {
            "brand": card["brand"] if card else None,
            "last_four": card["last_four"] if card else None,
            "expiry": card["expiry"].isoformat() if card and card["expiry"] else None,
            # Deliberately no token: attributes are recorded and end up in
            # traces, and the token is the one value that could start a charge.
            "cards_available": len(self.coordinator.data.payable_cards),
        }

    @property
    def selected_card(self) -> dict[str, Any] | None:
        """The card record behind the current option, if any."""
        for card in self.coordinator.data.payable_cards:
            if card_label(card) == self._selected:
                return card
        return None

    async def async_select_option(self, option: str) -> None:
        if option == NO_CARDS:
            return
        self._selected = option
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._sync_selection()
        super()._handle_coordinator_update()

    @callback
    def _sync_selection(self) -> None:
        """Keep the selection valid as cards are added, removed or expire.

        Mirrors the portal, which preselects the first non-expired card.
        """
        options = self.options
        if self._selected in options:
            return
        self._selected = options[0] if options and options[0] != NO_CARDS else None
