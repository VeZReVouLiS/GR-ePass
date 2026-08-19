"""Top-up flow for Attiki Odos e-Pass.

Home Assistant cannot charge a card. The e-PASS backend only *signs* an order
(``PrepAlphaPayment`` returns a ``Digest``); the money moves when those fields
are POSTed as a form to the bank's hosted page, where 3-D Secure runs and which
needs a real browser.

So this module does the half that can be automated: it asks for a signed order
and parks it behind a one-shot URL. Opening that URL shows what is about to be
charged and requires a click to hand off to the bank. The page deliberately does
NOT auto-submit -- that click is the last point where the user can back out.

Field names and values were verified against a real (blocked) submission from
the portal, so the digest matches: every signed value we put in the form is the
same value we sent in the prepare request.
"""

from __future__ import annotations

import logging
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from html import escape
from typing import Any

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .api import EpassClient
from .const import DOMAIN, EXT_TOKEN_STORED

_LOGGER = logging.getLogger(__name__)

PAY_URL = f"/api/{DOMAIN}/pay"

# Long enough that guessing is hopeless, short-lived, and single use.
NONCE_BYTES = 16
ORDER_TTL = timedelta(minutes=10)

# Static form values, taken from an observed submission. Everything the SPA
# leaves blank is blank here too -- the digest covers these, so they must match
# byte for byte.
STATIC_FIELDS: dict[str, str] = {
    "version": "2",
    "deviceCategory": "0",
    "billState": "",
    "weight": "",
    "dimensions": "",
    "shipCountry": "",
    "shipState": "",
    "shipZip": "",
    "shipCity": "",
    "shipAddress": "",
    "addFraudScore": "",
    "maxPayRetries": "",
    "reject3dsU": "",
    "payMethod": "",
    "trType": "",
    "extInstallmentoffset": "",
    "extInstallmentPeriod": "",
    "extRecurringfrequency": "",
    "extRecurringenddate": "",
    "blockScore": "",
    "cssUrl": "",
    "var1": "",
    "var2": "",
    "var3": "",
    "var4": "",
    "var5": "",
    # The terms checkbox lives inside the form, so it is submitted as well.
    "agreedToTOS": "on",
}

_NEWLINES = re.compile(r"\r\n|\r|\n")


def sanitize(value: Any) -> str:
    """Mirror the portal's sanitizeForPayment().

    Reproduced exactly rather than improved: the digest is computed over these
    strings, so any difference in normalisation would break the signature.
    """
    if value is None:
        return ""
    text = _NEWLINES.sub(" ", str(value))
    for old, new in (
        ('"', "'"),
        ("&amp;", "&"),
        ("&gt;", "-"),
        ("&lt;", "-"),
        ("&apos;", "'"),
        ("&quot;", "'"),
        ("\x00", ""),
    ):
        text = text.replace(old, new)
    return text


@dataclass
class PreparedOrder:
    """One signed order, waiting for a human to confirm it."""

    nonce: str
    action: str
    fields: dict[str, str]
    amount: float
    card_label: str
    created: datetime = field(default_factory=dt_util.utcnow)

    @property
    def expired(self) -> bool:
        return dt_util.utcnow() - self.created > ORDER_TTL


class EpassPaymentManager:
    """Prepares top-up orders and hands out one-shot confirmation links."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._orders: dict[str, PreparedOrder] = {}

    async def async_prepare(
        self,
        client: EpassClient,
        account: dict[str, Any],
        amount: float,
        card: dict[str, Any],
        card_label: str,
        language: str,
    ) -> PreparedOrder:
        """Ask the backend to sign an order and park it behind a nonce."""
        # SameBillingAsMailingAddress means the billing fields are empty and the
        # mailing ones stand in -- the portal copies them over before paying.
        if account.get("SameBillingAsMailingAddress"):
            city = account.get("MailingCity")
            address = account.get("MailingAddress")
            postal = account.get("MailingPostalCode")
        else:
            city = account.get("BillingCity")
            address = account.get("BillingAddress")
            postal = account.get("BillingPostalCode")

        # getCountryCode() defaults to "GR" and normalises the Greek code to it,
        # so there is no need to resolve the country list.
        amount_str = f"{amount:.2f}".rstrip("0").rstrip(".")
        lang = "el" if str(language).lower().startswith("el") else "en"

        request = {
            "AccountId": str(account.get("AccountID")),
            "Lang": lang,
            "DeviceCategory": STATIC_FIELDS["deviceCategory"],
            "BillingCountryCode": "GR",
            "BillingCity": sanitize(city),
            "BillingAddress": sanitize(address),
            "BillingPostalCode": sanitize(postal),
            "Amount": amount_str,
            "Currency": "EUR",
            "PhoneNo": "",
            "Email": account.get("Email") or "",
            "ExtTokenOptions": EXT_TOKEN_STORED,
            "ExtToken": card["token"],
            # getAlphaCardType() is "" for a stored card.
            "CardType": "",
        }
        signed = await client.async_prepare_payment(request)
        if not signed.get("Digest") or not signed.get("PostUrl"):
            raise ValueError(
                "The e-PASS backend did not return a signed order "
                f"(keys: {sorted(signed)})"
            )

        fields = dict(STATIC_FIELDS)
        fields.update(
            {
                "mid": signed.get("MerchantId", ""),
                "lang": lang,
                "orderid": signed.get("OrderId", ""),
                "orderDesc": signed.get("OrderDescription", ""),
                "orderAmount": amount_str,
                "orderAmountOriginal": amount_str,
                "currency": "EUR",
                "payerEmail": signed.get("Email") or request["Email"],
                "payerPhone": "",
                "billCountry": request["BillingCountryCode"],
                "billZip": request["BillingPostalCode"],
                "billCity": request["BillingCity"],
                "billAddress": request["BillingAddress"],
                "confirmUrl": signed.get("SuccessUrl", ""),
                "cancelUrl": signed.get("FailUrl", ""),
                "extTokenOptions": EXT_TOKEN_STORED,
                "extToken": card["token"],
                "digest": signed["Digest"],
            }
        )

        self._purge()
        order = PreparedOrder(
            nonce=secrets.token_urlsafe(NONCE_BYTES),
            action=signed["PostUrl"],
            fields=fields,
            amount=amount,
            card_label=card_label,
        )
        self._orders[order.nonce] = order
        _LOGGER.debug(
            "Prepared order %s for %.2f EUR", fields.get("orderid"), amount
        )
        return order

    def take(self, nonce: str) -> PreparedOrder | None:
        """Fetch and consume an order. One use only."""
        self._purge()
        return self._orders.pop(nonce, None)

    def peek(self, nonce: str) -> PreparedOrder | None:
        self._purge()
        return self._orders.get(nonce)

    def _purge(self) -> None:
        for nonce in [n for n, o in self._orders.items() if o.expired]:
            del self._orders[nonce]


class EpassPaymentView(HomeAssistantView):
    """Serves the confirmation page that hands the order to the bank.

    Unauthenticated on purpose: the link is meant to be tapped from a Telegram
    message on a phone, where there may be no Home Assistant session. What
    protects it is that the URL carries a 128-bit single-use nonce that expires
    in ten minutes, and that the amount and card were fixed when the order was
    signed -- the link cannot be edited into a different charge. The worst a
    leaked link can do is top up the owner's own toll balance.
    """

    url = PAY_URL + "/{nonce}"
    name = f"api:{DOMAIN}:pay"
    requires_auth = False

    def __init__(self, manager: EpassPaymentManager) -> None:
        self._manager = manager

    async def get(self, request, nonce: str):
        order = self._manager.peek(nonce)
        if order is None:
            return web.Response(
                text=_page_expired(), content_type="text/html", status=404
            )
        return web.Response(text=_page_confirm(order), content_type="text/html")

    async def post(self, request, nonce: str):
        """Consume the order; the returned page submits to the bank."""
        order = self._manager.take(nonce)
        if order is None:
            return web.Response(
                text=_page_expired(), content_type="text/html", status=404
            )
        return web.Response(text=_page_handoff(order), content_type="text/html")


_STYLE = """
  body { margin:0; font-family:system-ui,-apple-system,"Segoe UI",sans-serif;
         background:#f4f4f4; color:#14140f; }
  .wrap { max-width:420px; margin:0 auto; padding:24px 18px; }
  .card { background:#fff; border-radius:12px; overflow:hidden;
          box-shadow:0 1px 4px rgba(0,0,0,.15); }
  .head { background:#024e7e; color:#fff; padding:14px 18px;
          border-bottom:3px solid #fcbd02; font-weight:600; }
  .body { padding:18px; }
  .amount { font-size:32px; font-weight:700; margin:6px 0 2px; }
  .muted { color:#666; font-size:14px; }
  button { width:100%; margin-top:20px; padding:14px; border:none;
           border-radius:8px; background:#024e7e; color:#fff; font-size:16px;
           font-weight:600; cursor:pointer; }
  .note { font-size:12px; color:#666; margin-top:14px; line-height:1.45; }
"""


def _money(amount: float) -> str:
    """Greek decimal comma, e.g. 5,00 €.

    Done here rather than with locale formatting: the confirmation page is
    served by the integration and always reads in Greek, and relying on the
    host's locale would make the output depend on the container's environment.
    """
    return f"{amount:.2f}".replace(".", ",") + " €"


def _page_expired() -> str:
    return (
        "<!doctype html><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<style>{_STYLE}</style><div class='wrap'><div class='card'>"
        "<div class='head'>Αττική Οδός e-Pass</div><div class='body'>"
        "<p>Ο σύνδεσμος δεν ισχύει πλέον.</p>"
        "<p class='muted'>Κάθε σύνδεσμος πληρωμής χρησιμοποιείται μία φορά και "
        "λήγει μετά από 10 λεπτά. Ξεκίνα νέα ανανέωση από το Home Assistant."
        "</p></div></div></div>"
    )


def _page_confirm(order: PreparedOrder) -> str:
    """Step 1: show what will be charged. Nothing has happened yet."""
    return (
        "<!doctype html><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Ανανέωση e-Pass</title><style>{_STYLE}</style>"
        "<div class='wrap'><div class='card'>"
        "<div class='head'>Επιβεβαίωση ανανέωσης</div><div class='body'>"
        "<div class='muted'>Ποσό χρέωσης</div>"
        f"<div class='amount'>{_money(order.amount)}</div>"
        f"<div class='muted'>{escape(order.card_label)}</div>"
        "<form method='post'>"
        "<button type='submit'>Συνέχεια στην τράπεζα</button></form>"
        "<p class='note'>Πατώντας «Συνέχεια» θα μεταφερθείς στη σελίδα της "
        "Alpha Bank, όπου ολοκληρώνεται η χρέωση. Μέχρι τότε δεν έχει γίνει "
        "καμία κίνηση. Ο σύνδεσμος ισχύει για μία χρήση.</p>"
        "</div></div></div>"
    )


def _page_handoff(order: PreparedOrder) -> str:
    """Step 2: the actual hand-off. Auto-submits, since the user just agreed."""
    inputs = "".join(
        f"<input type='hidden' name='{escape(name)}' "
        f"value=\"{escape(str(value), quote=True)}\">"
        for name, value in order.fields.items()
    )
    return (
        "<!doctype html><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<style>{_STYLE}</style><div class='wrap'><div class='card'>"
        "<div class='head'>Μεταφορά στην τράπεζα…</div>"
        "<div class='body'><p class='muted'>Αν δεν μεταφερθείς αυτόματα, πάτα "
        "το κουμπί.</p>"
        f"<form id='f' method='POST' action='{escape(order.action, quote=True)}'>"
        f"{inputs}<button type='submit'>Συνέχεια</button></form>"
        "</div></div></div>"
        "<script>document.getElementById('f').submit();</script>"
    )
