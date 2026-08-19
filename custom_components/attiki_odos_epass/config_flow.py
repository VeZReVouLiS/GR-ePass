"""Config and options flow for Attiki Odos e-PASS."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import EpassAuthError, EpassClient, EpassConnectionError, EpassError
from .const import (
    ALL_TRANSPONDERS,
    CONF_ACCOUNT_ID,
    CONF_SCAN_INTERVAL_MINUTES,
    CONF_TRANSPONDERS,
    DOMAIN,
    MAX_SCAN_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
)
from .coordinator import transponder_key, transponder_label

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="username")
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)


def account_id_of(account: dict[str, Any]) -> str:
    """Read the account id regardless of the casing the backend used.

    GetUserAccountsInfo and GetAccount do not agree on the key: the list
    endpoint returns AccountID while other responses have been seen with
    AccountId. Probing a few spellings is cheaper than guessing wrong.
    """
    for name in ("AccountID", "AccountId", "accountId", "AccountNumber"):
        if account.get(name) not in (None, ""):
            return str(account[name])
    return ""


def account_label(account: dict[str, Any]) -> str:
    """Readable label for an account picker entry."""
    account_id = account_id_of(account)
    for name in ("AccountAlias", "AccountName", "UserGroupName"):
        if account.get(name):
            return f"{account[name]} ({account_id})"
    names = " ".join(
        str(account[key])
        for key in ("FirstName", "LastName")
        if account.get(key)
    ).strip()
    if names:
        return f"{names} ({account_id})"
    return account_id or "e-PASS"


# Selector option labels are literal strings -- a translation_key only works for
# a fixed option list, and the transponder list is discovered per account. So the
# one static entry picks its own wording from the Home Assistant language.
ALL_LABEL = {"el": "Όλοι", "en": "All"}


def transponder_options(
    transponders: list[dict[str, Any]], language: str = "en"
) -> list[SelectOptionDict]:
    """Build the multi-select options, with an explicit "all" entry first.

    Choosing "all" stores a sentinel rather than the current ids, so transponders
    added to the subscription later are picked up without reconfiguring.
    """
    lang = "el" if str(language).lower().startswith("el") else "en"
    options = [SelectOptionDict(value=ALL_TRANSPONDERS, label=ALL_LABEL[lang])]
    for transponder in transponders:
        key = transponder_key(transponder)
        label = transponder_label(transponder)
        plate = transponder.get("PlateNum")
        display = transponder.get("TransponderDisplayId") or key
        detail = " · ".join(
            str(part) for part in (plate, display) if part and str(part) != label
        )
        options.append(
            SelectOptionDict(
                value=key, label=f"{label} ({detail})" if detail else label
            )
        )
    return options


class EpassConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup."""

    VERSION = 1

    def __init__(self) -> None:
        self._username: str = ""
        self._password: str = ""
        self._accounts: list[dict[str, Any]] = []
        self._account: dict[str, Any] = {}
        self._transponders: list[dict[str, Any]] = []

    # ------------------------------------------------------------- user step

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._username = user_input[CONF_USERNAME].strip()
            self._password = user_input[CONF_PASSWORD]
            client = self._client()
            try:
                await client.async_login()
                self._accounts = await client.async_get_accounts()
            except EpassAuthError:
                errors["base"] = "invalid_auth"
            except EpassConnectionError:
                errors["base"] = "cannot_connect"
            except EpassError:
                _LOGGER.exception("Unexpected error talking to my e-PASS")
                errors["base"] = "unknown"
            else:
                if not self._accounts:
                    return self.async_abort(reason="no_accounts")
                if len(self._accounts) == 1:
                    self._account = self._accounts[0]
                    return await self.async_step_transponders()
                return await self.async_step_account()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    # ---------------------------------------------------------- account step

    async def async_step_account(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            chosen = user_input[CONF_ACCOUNT_ID]
            self._account = next(
                (
                    account
                    for account in self._accounts
                    if account_id_of(account) == chosen
                ),
                {},
            )
            if not self._account:
                return self.async_abort(reason="no_accounts")
            return await self.async_step_transponders()

        options = [
            SelectOptionDict(value=account_id_of(a), label=account_label(a))
            for a in self._accounts
            if account_id_of(a)
        ]
        schema = vol.Schema(
            {
                vol.Required(CONF_ACCOUNT_ID): SelectSelector(
                    SelectSelectorConfig(
                        options=options, mode=SelectSelectorMode.DROPDOWN
                    )
                )
            }
        )
        return self.async_show_form(step_id="account", data_schema=schema)

    # ----------------------------------------------------- transponders step

    async def async_step_transponders(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        account_id = account_id_of(self._account)
        # Username plus account id: one web user can hold several subscriptions,
        # and the same subscription can be reachable by more than one user, so
        # neither half is unique on its own.
        await self.async_set_unique_id(f"{self._username.lower()}:{account_id}")
        self._abort_if_unique_id_configured()

        if user_input is not None:
            selection = user_input.get(CONF_TRANSPONDERS) or [ALL_TRANSPONDERS]
            return self.async_create_entry(
                title=f"e-PASS {account_label(self._account)}",
                data={
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                    CONF_ACCOUNT_ID: account_id,
                    CONF_TRANSPONDERS: selection,
                },
            )

        if not self._transponders:
            client = self._client()
            try:
                await client.async_login()
                self._transponders = await client.async_get_transponders(account_id)
            except EpassAuthError:
                return self.async_abort(reason="invalid_auth")
            except (EpassConnectionError, EpassError):
                return self.async_abort(reason="cannot_connect")

        if not self._transponders:
            return self.async_abort(reason="no_transponders")

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_TRANSPONDERS, default=[ALL_TRANSPONDERS]
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=transponder_options(
                            self._transponders, self.hass.config.language
                        ),
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(
            step_id="transponders",
            data_schema=schema,
            description_placeholders={"count": str(len(self._transponders))},
        )

    # --------------------------------------------------------------- reauth

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        self._username = entry_data[CONF_USERNAME]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            client = EpassClient(
                async_create_clientsession(self.hass),
                entry.data[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            try:
                await client.async_login()
            except EpassAuthError:
                errors["base"] = "invalid_auth"
            except (EpassConnectionError, EpassError):
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    )
                }
            ),
            errors=errors,
            description_placeholders={"username": entry.data[CONF_USERNAME]},
        )

    # -------------------------------------------------------------- helpers

    def _client(self) -> EpassClient:
        return EpassClient(
            async_create_clientsession(self.hass), self._username, self._password
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: Any) -> EpassOptionsFlow:
        return EpassOptionsFlow()


class EpassOptionsFlow(OptionsFlow):
    """Let the user change the transponder selection and the poll interval."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self.config_entry
        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_TRANSPONDERS: user_input.get(CONF_TRANSPONDERS)
                    or [ALL_TRANSPONDERS],
                    CONF_SCAN_INTERVAL_MINUTES: int(
                        user_input[CONF_SCAN_INTERVAL_MINUTES]
                    ),
                }
            )

        # Fetched live rather than read from the coordinator: the options flow
        # can be opened while the entry is in a failed state, and a fresh list is
        # what makes newly added transponders selectable.
        client = EpassClient(
            async_create_clientsession(self.hass),
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )
        try:
            await client.async_login()
            transponders = await client.async_get_transponders(
                entry.data[CONF_ACCOUNT_ID]
            )
        except (EpassAuthError, EpassConnectionError, EpassError):
            # An empty list still lets the user change the interval; better than
            # refusing to open the dialog at all.
            transponders = []

        current = entry.options.get(
            CONF_TRANSPONDERS, entry.data.get(CONF_TRANSPONDERS, [ALL_TRANSPONDERS])
        )
        known = {transponder_key(t) for t in transponders}
        # Drop stale ids so the selector does not choke on unknown values.
        current = [
            value
            for value in current
            if value == ALL_TRANSPONDERS or value in known
        ] or [ALL_TRANSPONDERS]

        schema = vol.Schema(
            {
                vol.Required(CONF_TRANSPONDERS, default=current): SelectSelector(
                    SelectSelectorConfig(
                        options=transponder_options(
                            transponders, self.hass.config.language
                        ),
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
                vol.Required(
                    CONF_SCAN_INTERVAL_MINUTES,
                    default=entry.options.get(CONF_SCAN_INTERVAL_MINUTES, 30),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL_MINUTES,
                        max=MAX_SCAN_INTERVAL_MINUTES,
                        step=5,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
