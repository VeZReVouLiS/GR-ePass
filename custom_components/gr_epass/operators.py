"""The toll operators this integration can talk to.

Greek prepaid toll accounts are run on one shared platform, deployed once per
operator. Both deployments were compared field by field: the same Angular client,
the same thirteen API controllers, the same signature endpoints down to
``IbiSystemIntegrityCheck``, and ``assets/clientConfig.json`` files that differ
only in branding. Neither declares a ``serverUrl``, so each talks to its own
origin. That is why one client works for all of them and the operator is just a
base url plus a few labels.

Adding another operator means adding an entry here. Confirm first that its
portal serves ``assets/clientConfig.json`` and that its bundle contains
``api/alphaPaym`` -- if it does, it is the same platform.

Toll limits are deliberately optional. They come from an operator's published
price list, not from the API, so inventing them for an operator whose list has
not been read would put confident wrong numbers in front of someone deciding
when to top up.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

# Category 1 is a car, 5 and 6 are the heaviest classes. Read from the operator's
# published price list; nothing at runtime depends on them.
_ATTIKI_LIMITS: Mapping[int, Mapping[str, float]] = MappingProxyType(
    {
        1: MappingProxyType({"recharge": 10.00, "low_balance": 6.00, "invalid": 1.25}),
        2: MappingProxyType({"recharge": 20.00, "low_balance": 12.00, "invalid": 2.55}),
        3: MappingProxyType({"recharge": 20.00, "low_balance": 12.00, "invalid": 2.55}),
        4: MappingProxyType({"recharge": 20.00, "low_balance": 12.00, "invalid": 2.55}),
        5: MappingProxyType({"recharge": 50.00, "low_balance": 40.00, "invalid": 10.10}),
        6: MappingProxyType({"recharge": 50.00, "low_balance": 40.00, "invalid": 10.10}),
    }
)

# Used when an operator publishes no limits we have read. Deliberately low so it
# never reads as advice: it is only a starting value for the threshold the user
# sets themselves.
FALLBACK_LOW_BALANCE = 10.00


@dataclass(frozen=True, kw_only=True)
class Operator:
    """One deployment of the toll platform."""

    key: str
    name: str
    base_url: str
    payment_path: str
    # Header and accent, taken from the operator's own clientConfig.json so the
    # page looks like the portal it is talking to.
    navy: str
    accent: str
    toll_limits: Mapping[int, Mapping[str, float]] | None = None
    limits_source: str | None = None

    @property
    def portal_url(self) -> str:
        return f"{self.base_url}/"

    @property
    def payment_url(self) -> str:
        return f"{self.base_url}{self.payment_path}"

    def limits_for(self, category: int) -> Mapping[str, float] | None:
        """Published limits for a vehicle category, if this operator has any."""
        if self.toll_limits is None:
            return None
        return self.toll_limits.get(category)


ATTIKI = Operator(
    key="attiki",
    name="Νέα Αττική Οδός",
    base_url="https://epass.naodos.gr",
    payment_path="/PaymentA",
    navy="#024e7e",
    accent="#fcbd02",
    toll_limits=_ATTIKI_LIMITS,
    limits_source="Τιμοκατάλογος Prepaid e-PASS, naodos.gr, 01/01/2026",
)

EGNATIA = Operator(
    key="egnatia",
    name="Νέα Εγνατία Οδός",
    base_url="https://myegnatiapass.gr",
    payment_path="/PaymentA",
    # From its clientConfig.json: --darkPrimary-color and --primary-color.
    navy="#2b447e",
    accent="#a8de20",
    # Its price list has not been read, so no limits are claimed here.
)

OPERATORS: Mapping[str, Operator] = MappingProxyType(
    {operator.key: operator for operator in (ATTIKI, EGNATIA)}
)

DEFAULT_OPERATOR = ATTIKI.key


def get_operator(key: str | None) -> Operator:
    """Resolve a stored operator key.

    Entries created before operators existed carry no key and are all Attiki
    Odos, which is why an unknown or missing key falls back to it rather than
    failing the setup.
    """
    return OPERATORS.get(key or DEFAULT_OPERATOR, ATTIKI)
