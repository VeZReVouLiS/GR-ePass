"""Constants for the Attiki Odos e-PASS integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "gr_epass"

# --- Reverse engineered from the my e-PASS Angular SPA -----------------------
# The SPA loads assets/clientConfig.json, which has no "serverUrl" key, so the
# Angular proxy base URL resolves to "" and every call is same-origin.
TOKEN_PATH = "/oauth2/token"
CLIENT_ID = "100"  # clientConfig.json -> ClientId
CLIENT_SECRET = "secret"  # hardcoded in the SPA bundle

CONF_OPERATOR = "operator"
CONF_ACCOUNT_ID = "account_id"
CONF_TRANSPONDERS = "transponders"
CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"

ALL_TRANSPONDERS = "__all__"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)
MIN_SCAN_INTERVAL_MINUTES = 10
MAX_SCAN_INTERVAL_MINUTES = 1440

# The web UI refuses ranges wider than 30 days (daysLimitAO = 30).
MAX_RANGE_DAYS = 30

# databaseMapService.eAccountTransactionTypeMap
TXN_PAYMENT = "01"
TXN_TOLL_CHARGE = "02"
TXN_TRANSPONDER_CHARGE = "03"
TXN_ADMIN_CHARGE = "04"
TXN_ADJUSTMENT = "05"
TXN_REFUND = "06"
TXN_TAX = "07"
TXN_ADJUSTMENT_CREDIT = "08"
TXN_ADJUSTMENT_DEBIT = "09"

TRANSACTION_TYPES = {
    TXN_PAYMENT: "payment",
    TXN_TOLL_CHARGE: "toll_charge",
    TXN_TRANSPONDER_CHARGE: "transponder_charge",
    TXN_ADMIN_CHARGE: "administration_charge",
    TXN_ADJUSTMENT: "adjustment",
    TXN_REFUND: "refund",
    TXN_TAX: "tax",
    TXN_ADJUSTMENT_CREDIT: "adjustment_credit",
    TXN_ADJUSTMENT_DEBIT: "adjustment_debit",
}

# databaseMapService.eBalanceStatusMap.
# GetAccount returns this as an int; note that GetUserAccountsInfo returns a
# letter ("G") for the same concept, which is why only the detail record is used.
BALANCE_STATUS = {1: "good", 2: "low", 3: "bad"}

# databaseMapService.eAccountStatusMap
ACCOUNT_STATUS = {
    1: "incomplete",
    2: "inactive",
    3: "active_partial",
    4: "active",
    5: "closed",
}

# The Transponders page renders a green check when RestrictionStatus == 2 and a
# warning icon otherwise. Its label goes through eTransponderRestrictionMap,
# which getMapValue() does not implement, so the portal itself shows no text --
# the icon is the only real signal, hence just these two states.
TRANSPONDER_RESTRICTION_OK = 2
TRANSPONDER_STATES = ["active", "restricted"]

# --- Payments (Alpha Bank gateway, controller api/alphaPaym) ------------------
# The e-PASS backend only *prepares* a signed order; the actual charge is a
# browser form POST to the bank's hosted page (PostUrl), where 3-D Secure runs.
# There is no endpoint that charges a stored card server-side.
STORED_CARDS_PATH = "/api/alphaPaym/GetStoredCards"
PAYMENT_PROVIDER_PATH = "/api/alphaPaym/GetPaymProviderInfo"
PAYMENT_PREPARE_PATH = "/api/alphaPaym/PrepAlphaPayment"
TXN_RECEIPT_PATH = "/api/alphaPaym/GetTxnReceipt"

# databaseMapService.eOCardTypeMap
CARD_TYPES = {
    0: "other",
    1: "visa",
    2: "mastercard",
    3: "maestro",
    4: "amex",
    5: "diners",
}

# getTokenParameter() in the SPA decides what happens to the card token:
#   "110" -> pay with a card that is already stored
#   "100" -> pay with a new card and store it for next time
# A stored card also needs CardType = "" (getAlphaCardType()).
EXT_TOKEN_STORED = "110"
EXT_TOKEN_SAVE = "100"

# Stored-card lifecycle, mirroring getEffectiveState() on the Bank Cards page.
CARD_STATE_ACTIVE = "active"
CARD_STATE_INACTIVE = "inactive"
CARD_STATE_EXPIRED = "expired"

# --- Published account limits ------------------------------------------------
# Snapshot of the "Τιμοκατάλογος Prepaid e-PASS" published on naodos.gr,
# effective 2026-01-01. Categories 2-4 share one column and 5-6 share another.
#
#   recharge     Όριο Ανανέωσης Λογαριασμού με Πιστωτική Κάρτα — the balance at
#                which the operator's standing order (πάγια εντολή) tops the
#                account up, when the subscriber has one set up.
#   low_balance  Όριο Ειδοποίησης Χαμηλού Λογαριασμού — where BalanceStatus
#                flips from 1 (good) to 2 (low).
#   invalid      Όριο Άκυρου Λογαριασμού — below this NO subscriber pass is
#                allowed; you must use a staffed lane. Equals one toll fee.
#
# These are only used to suggest a sensible default threshold. They are a
# published price list and can change, so nothing depends on them at runtime.
# --- Events ------------------------------------------------------------------
# Fired on the HA event bus so users can automate without the integration
# having to guess which notification channel they want.
EVENT_PASS = f"{DOMAIN}_pass"
EVENT_BALANCE_CHANGED = f"{DOMAIN}_balance_changed"
# Fired when a top-up order has been signed and a confirmation link exists.
EVENT_PAYMENT_READY = f"{DOMAIN}_payment_ready"

# A pass older than this is treated as backfill and does not raise an event,
# so a restart or a widened fetch window cannot replay old history.
EVENT_PASS_MAX_AGE = timedelta(hours=6)
