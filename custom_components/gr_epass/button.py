"""Prepare a top-up for GR e-Pass.

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
from .const import CONF_NOTIFY_AUTO, EVENT_PAYMENT_READY
from .coordinator import EpassCoordinator
from .entity import account_device_info
from .notifier import async_send_link
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
        self._attr_device_info = account_device_info(account_id, coordinator.operator)
        # The sender and the page reach the current link through here.
        coordinator.topup_button = self
        self._link: str | None = None
        self._link_expires: str | None = None
        # How the last order ended, and when. The page needs both: it says
        # "cancelled" only for a little while, since there is no state change
        # later to take the message away again.
        self._link_result: str | None = None
        self._link_result_at: str | None = None
        self._nonce: str | None = None
        self._amount: float | None = None
        self._card_label: str | None = None
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
            "link_result": self._link_result,
            "link_result_at": self._link_result_at,
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
        amount = self._selected_amount()
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
        self._link_result = None
        self._link_result_at = None
        self._amount = amount
        self._card_label = card_label
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
        await self._async_maybe_notify()

    @property
    def link(self) -> str | None:
        """The confirmation link, while one is live."""
        return self._link

    @property
    def amount_text(self) -> str:
        """The amount as the reader writes it: comma in Greek, point in English."""
        if self._amount is None:
            return "—"
        text = f"{self._amount:.2f}"
        if (self.hass.config.language or "").startswith("el"):
            text = text.replace(".", ",")
        return f"{text} €"

    @property
    def card_text(self) -> str:
        return self._card_label or "—"

    @property
    def minutes_left(self) -> int:
        """Whole minutes before the link expires, never negative."""
        if not self._link_expires:
            return 0
        remaining = dt_util.parse_datetime(self._link_expires)
        if remaining is None:
            return 0
        seconds = (remaining - dt_util.now()).total_seconds()
        return max(0, int(seconds // 60))

    async def _async_maybe_notify(self) -> None:
        """Send the link straight away when the user asked for that.

        Failures are logged rather than raised: the link is prepared and shown on
        the page either way, and a broken notifier must not look like a failed
        top-up.
        """
        entry = self.coordinator.config_entry
        if not entry.options.get(CONF_NOTIFY_AUTO):
            return
        try:
            await async_send_link(self.hass, entry, self.coordinator)
        except Exception as err:  # noqa: BLE001 - reported, not fatal
            _LOGGER.warning("Could not send the payment link: %s", err)

    def _release(self) -> None:
        """Stop watching the current order without touching the shown link."""
        if self._unsub_expiry is not None:
            self._unsub_expiry()
            self._unsub_expiry = None
        manager = self.coordinator.payment
        if manager is not None and self._nonce is not None:
            manager.unwatch(self._nonce)

    def _drop_link(self, reason: str = "expired") -> None:
        """Forget the link, remembering how the order ended."""
        self._release()
        self._nonce = None
        self._link = None
        self._link_expires = None
        self._link_result = reason
        self._link_result_at = dt_util.utcnow().isoformat()
        self.async_write_ha_state()

    def _on_expired(self, _now) -> None:
        self._unsub_expiry = None
        self._drop_link("expired")

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
                "γίνει στο portal του παρόχου με «αποθήκευση κάρτας»."
            )
        picker = self.coordinator.card_select
        card = picker.selected_card if picker is not None else None
        if card is None:
            # Selection stale or not restored yet: fall back the way the portal
            # does, to the first usable card.
            card = cards[0]
        return card, make_label(card)

    def _selected_amount(self) -> float:
        """Amount chosen on the number entity.

        Not named `_amount`: that is the attribute holding the amount of the
        order already prepared, and an attribute silently wins over a method
        of the same name.
        """
        entity = self.coordinator.amount_entity
        value = entity.native_value if entity is not None else None
        if value is None:
            raise HomeAssistantError("Δεν έχει οριστεί ποσό ανανέωσης")
        return round(float(value), 2)
