"""Prepare a top-up for Attiki Odos e-Pass.

Pressing this does not charge anything. It asks the e-PASS backend to sign an
order for the selected card and amount, then publishes a one-shot confirmation
link. The charge only happens after someone opens that link and presses the
button on it, which hands the order to the bank's hosted page.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.network import NoURLAvailableError, get_url
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import EpassConfigEntry
from .const import EVENT_PAYMENT_READY
from .coordinator import EpassCoordinator
from .entity import account_device_info
from .payment import ORDER_TTL, PAY_URL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EpassConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the prepare-top-up button."""
    coordinator = entry.runtime_data
    async_add_entities(
        [EpassPrepareTopUp(coordinator, str(coordinator.account_id))]
    )


class EpassPrepareTopUp(CoordinatorEntity[EpassCoordinator], ButtonEntity):
    """Signs a top-up order and publishes a confirmation link."""

    _attr_has_entity_name = True
    _attr_translation_key = "prepare_topup"
    _attr_icon = "mdi:cash-fast"

    def __init__(self, coordinator: EpassCoordinator, account_id: str) -> None:
        super().__init__(coordinator)
        self._account_id = account_id
        self._attr_unique_id = f"{account_id}_prepare_topup"
        self._attr_device_info = account_device_info(account_id)
        self._link: str | None = None
        self._link_expires: str | None = None
        self._nonce: str | None = None
        self._unsub_expiry: Callable[[], None] | None = None

    @property
    def available(self) -> bool:
        # Nothing to prepare without a tokenised card: the first charge has to
        # happen on the portal so the bank can mint a token.
        return super().available and bool(self.coordinator.data.payable_cards)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        manager = self.coordinator.payment
        return {
            "link": self._link,
            "link_expires": self._link_expires,
            # Exposed so the page can offer the receipt for the payment that was
            # just made. The bank sends the payer to the operator's own receipt
            # page, which needs a portal login, so this is the only handle we
            # have on it.
            "last_order_id": manager.last_handoff if manager is not None else None,
        }

    async def async_press(self) -> None:
        """Sign an order. No money moves here."""
        coordinator = self.coordinator
        manager = coordinator.payment
        if manager is None:
            raise HomeAssistantError("Payment support is not set up")

        card, card_label = self._selected_card()
        amount = self._amount()
        self._check_gateway_bounds(amount)

        order = await manager.async_prepare(
            client=coordinator.client,
            account=coordinator.data.account,
            amount=amount,
            card=card,
            card_label=card_label,
            language=self.hass.config.language,
        )

        try:
            base = get_url(self.hass, allow_external=True, prefer_external=True)
        except NoURLAvailableError as err:
            raise HomeAssistantError(
                "Δεν υπάρχει προσβάσιμο URL για το Home Assistant — όρισε "
                "External URL στις ρυθμίσεις δικτύου"
            ) from err

        # A previous order is replaced, so stop listening for the old one.
        self._release()
        self._nonce = order.nonce
        self._link = f"{base}{PAY_URL}/{order.nonce}"
        self._link_expires = dt_util.as_local(order.created + ORDER_TTL).isoformat()
        # The link has to disappear once it cannot be used again, or the page
        # keeps offering a press that can only fail. Two things end an order:
        # someone uses it, which the manager reports, and the clock running out,
        # which nothing reports because a purge only happens if some other call
        # passes through the manager -- hence the timer as well.
        manager.watch(order.nonce, self._drop_link)
        self._unsub_expiry = async_call_later(
            self.hass, ORDER_TTL.total_seconds(), self._on_expired
        )
        self.async_write_ha_state()

        self.hass.bus.async_fire(
            EVENT_PAYMENT_READY,
            {
                "account_id": self._account_id,
                "amount": amount,
                "card": card_label,
                "order_id": order.fields.get("orderid"),
                "link": self._link,
                "expires": self._link_expires,
            },
        )
        _LOGGER.debug("Top-up link published for %.2f EUR", amount)

    def _release(self) -> None:
        """Stop watching the current order without touching the shown link."""
        if self._unsub_expiry is not None:
            self._unsub_expiry()
            self._unsub_expiry = None
        manager = self.coordinator.payment
        if manager is not None and self._nonce is not None:
            manager.unwatch(self._nonce)

    def _drop_link(self) -> None:
        """Forget the link. Called when the order is used or purged."""
        self._release()
        self._nonce = None
        self._link = None
        self._link_expires = None
        self.async_write_ha_state()

    def _on_expired(self, _now) -> None:
        self._unsub_expiry = None
        self._drop_link()

    async def async_will_remove_from_hass(self) -> None:
        self._release()
        await super().async_will_remove_from_hass()

    def _check_gateway_bounds(self, amount: float) -> None:
        limits = self.coordinator.data.payment_limits
        low, high = limits.get("min_amount"), limits.get("max_amount")
        if low is not None and amount < float(low):
            raise HomeAssistantError(
                f"Το ποσό {amount:.2f} € είναι κάτω από το ελάχιστο "
                f"{float(low):.2f} € του gateway"
            )
        if high is not None and amount > float(high):
            raise HomeAssistantError(
                f"Το ποσό {amount:.2f} € είναι πάνω από το μέγιστο "
                f"{float(high):.2f} € του gateway"
            )

    def _selected_card(self) -> tuple[dict[str, Any], str]:
        """Card chosen on the select entity, read through the coordinator.

        Going through the coordinator rather than composing an entity_id means a
        renamed entity does not break the flow.
        """
        from .select import card_label as make_label

        cards = self.coordinator.data.payable_cards
        if not cards:
            raise HomeAssistantError(
                "Δεν υπάρχει αποθηκευμένη κάρτα. Η πρώτη χρέωση πρέπει να "
                "γίνει στο epass.naodos.gr με «αποθήκευση κάρτας»."
            )
        picker = self.coordinator.card_select
        card = picker.selected_card if picker is not None else None
        if card is None:
            # Selection stale or not restored yet: fall back the way the portal
            # does, to the first usable card.
            card = cards[0]
        return card, make_label(card)

    def _amount(self) -> float:
        entity = self.coordinator.amount_entity
        value = entity.native_value if entity is not None else None
        if value is None:
            raise HomeAssistantError("Δεν έχει οριστεί ποσό ανανέωσης")
        return round(float(value), 2)
