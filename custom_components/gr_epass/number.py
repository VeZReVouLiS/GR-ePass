"""Adjustable numbers for GR e-PASS.

Two controls, both defaulting to figures the operator publishes for the vehicle
category of the monitored transponders, so a fresh install is already sensible
for a small car or a truck without the user looking anything up.
"""

from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EpassConfigEntry
from .coordinator import EpassCoordinator
from .entity import account_device_info

# Only used before the gateway has answered; the real bounds come from
# GetPaymProviderInfo and are deliberately not narrowed. The gateway allows
# 0.01-5000, so any amount the portal accepts is accepted here too.
FALLBACK_MIN = 0.01
FALLBACK_MAX = 5000.0

# Fallbacks for when the transponder record carries no usable category.
DEFAULT_TOPUP = 20.0
DEFAULT_LOW_BALANCE = 12.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EpassConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the adjustable numbers."""
    coordinator = entry.runtime_data
    account_id = str(coordinator.account_id)
    async_add_entities(
        [
            EpassTopUpAmount(coordinator, account_id),
            EpassLowBalanceThreshold(coordinator, account_id),
        ]
    )


class _EpassNumber(CoordinatorEntity[EpassCoordinator], NumberEntity, RestoreEntity):
    """A number the user can change, remembered across restarts."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "EUR"
    # Without the device class the frontend prints a bare "12.0 EUR"; with it the
    # value is formatted as currency, matching the monetary sensors beside it.
    _attr_device_class = NumberDeviceClass.MONETARY
    _attr_mode = NumberMode.BOX

    def __init__(
        self, coordinator: EpassCoordinator, account_id: str, key: str
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{account_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = account_device_info(account_id, coordinator.operator)
        self._value: float | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in (None, "", "unknown", "unavailable"):
            try:
                self._value = float(last.state)
            except ValueError:
                self._value = None
        if self._value is None:
            self._value = self._default()

    def _default(self) -> float:
        raise NotImplementedError

    @property
    def native_value(self) -> float | None:
        return self._value

    async def async_set_native_value(self, value: float) -> None:
        self._value = round(value, 2)
        self.async_write_ha_state()


class EpassTopUpAmount(_EpassNumber):
    """How much the next top-up should be for."""

    _attr_icon = "mdi:cash-plus"
    # Cent granularity, because the gateway's minimum is 0.01 -- a step of 1
    # would make every selectable value land on x.01.
    _attr_native_step = 0.01

    def __init__(self, coordinator: EpassCoordinator, account_id: str) -> None:
        super().__init__(coordinator, account_id, "topup_amount")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # The prepare-top-up button reads the amount through the coordinator
        # instead of composing an entity_id, so renames keep working.
        self.coordinator.amount_entity = self

    def _default(self) -> float:
        """Default to the category's own recharge limit.

        That is the balance at which the operator's standing order would top the
        account up, so it is a sensible amount to add in one go.
        """
        limits = self.coordinator.account_limits
        return float(limits.get("recharge", DEFAULT_TOPUP))

    @property
    def native_min_value(self) -> float:
        """Whatever the gateway allows -- no extra floor of our own.

        GetPaymProviderInfo reports 0.01 and a 1 EUR top-up really does go
        through, so narrowing this would only block something the service
        permits.
        """
        gateway = self.coordinator.data.payment_limits.get("min_amount")
        return float(gateway) if gateway else FALLBACK_MIN

    @property
    def native_max_value(self) -> float:
        gateway = self.coordinator.data.payment_limits.get("max_amount")
        return float(gateway) if gateway else FALLBACK_MAX


class EpassLowBalanceThreshold(_EpassNumber):
    """Balance below which the user wants to be warned.

    Shipped as an entity rather than left to a hand-made input_number helper so
    that every install gets a threshold matching its own vehicle category, and
    so dashboards and automations have something stable to reference.
    """

    _attr_icon = "mdi:bell-alert-outline"
    _attr_native_step = 0.5
    _attr_native_min_value = 0
    _attr_native_max_value = 500

    def __init__(self, coordinator: EpassCoordinator, account_id: str) -> None:
        super().__init__(coordinator, account_id, "low_balance_threshold")

    def _default(self) -> float:
        """The operator's own "low account" limit for this category."""
        limits = self.coordinator.account_limits
        return float(limits.get("low_balance", DEFAULT_LOW_BALANCE))

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        limits = self.coordinator.account_limits
        return {
            "toll_categories": self.coordinator.toll_categories,
            "official_low_balance_limit": limits.get("low_balance"),
            "official_invalid_limit": limits.get("invalid"),
            "limits_source": self.coordinator.operator.limits_source,
        }
