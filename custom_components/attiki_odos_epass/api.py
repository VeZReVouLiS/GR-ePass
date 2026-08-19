"""Thin async client for the (undocumented) my e-PASS web API of Attiki Odos.

Everything here was derived from the public Angular bundle served by
https://epass.naodos.gr -- there is no official API. Endpoints, payload shapes
and enum values may change without notice.

Auth flow
---------
POST /oauth2/token   grant_type=password   -> access_token (JWT) + refresh_token
POST /oauth2/token   grant_type=refresh_token
Every API call carries ``Authorization: Bearer <access_token>`` plus an empty
``gid`` header (the SPA puts a reCAPTCHA token there, but reCAPTCHA is disabled
for this client because clientConfig.json has no ``GoogleRecaptch`` key).
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import aiohttp
from aiohttp import ClientError, ClientResponseError

from .const import (
    BASE_URL,
    CLIENT_ID,
    CLIENT_SECRET,
    MAX_RANGE_DAYS,
    PAYMENT_PREPARE_PATH,
    PAYMENT_PROVIDER_PATH,
    STORED_CARDS_PATH,
    TOKEN_PATH,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=45)

# Refresh a little before the token actually dies.
TOKEN_LEEWAY = timedelta(seconds=90)

_JS_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_JS_MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


class EpassError(Exception):
    """Base error for the e-PASS client."""


class EpassAuthError(EpassError):
    """Credentials were rejected, or the session could not be renewed."""


class EpassConnectionError(EpassError):
    """The service could not be reached."""


def _js_date_string(value: datetime) -> str:
    """Render a datetime the way the JavaScript Date.toString() would.

    The SPA sends both an ISO string and this human readable form. The server
    appears to only use the ISO one, but we mirror the payload exactly.
    """
    offset = value.utcoffset() or timedelta(0)
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    return (
        f"{_JS_DAYS[value.weekday()]} {_JS_MONTHS[value.month - 1]} "
        f"{value.day:02d} {value.year} {value:%H:%M:%S} "
        f"GMT{sign}{total_minutes // 60:02d}{total_minutes % 60:02d}"
    )


def _iso_z(value: datetime) -> str:
    """Serialise a datetime the way JSON.stringify(new Date()) does."""
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _decode_jwt_payload(token: str) -> dict[str, Any]:
    """Read a JWT payload without verifying it. We only need exp and profile."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except (IndexError, ValueError, binascii.Error, UnicodeDecodeError):
        return {}


def _token_error_message(body: str) -> str:
    """Turn an OAuth error body into something readable."""
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return "Invalid username or password"
    error = data.get("error", "")
    if error == "invalid_grant":
        return "Invalid username or password"
    return data.get("error_description") or error or "Authentication failed"


class EpassClient:
    """Talks to the my e-PASS backend on behalf of one web user."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: datetime | None = None
        self._lock = asyncio.Lock()
        self.user_profile: dict[str, Any] = {}

    # ------------------------------------------------------------------ auth

    async def async_login(self) -> None:
        """Obtain a fresh token pair with the password grant."""
        await self._async_token_request(
            {
                "username": self._username,
                "password": self._password,
                "grant_type": "password",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "stay_signed_in": "true",
            }
        )

    async def _async_refresh(self) -> None:
        """Renew the access token, falling back to a full login."""
        if not self._refresh_token:
            await self.async_login()
            return
        try:
            await self._async_token_request(
                {
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                }
            )
        except EpassAuthError:
            _LOGGER.debug("Refresh token rejected, logging in again")
            self._refresh_token = None
            await self.async_login()

    async def _async_token_request(self, payload: dict[str, str]) -> None:
        headers = {
            # Yes, without the "application/" prefix. That is what the SPA
            # sends and what the backend expects.
            "Content-Type": "x-www-form-urlencoded",
            "Audience": "Any",
        }
        try:
            async with self._session.post(
                f"{BASE_URL}{TOKEN_PATH}",
                data=urlencode(payload),
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                body = await resp.text()
                if resp.status in (400, 401):
                    raise EpassAuthError(_token_error_message(body))
                if resp.status >= 400:
                    raise EpassError(f"Token endpoint returned HTTP {resp.status}")
                data = json.loads(body)
        except (ClientError, asyncio.TimeoutError) as err:
            raise EpassConnectionError(f"Cannot reach {BASE_URL}: {err}") from err
        except json.JSONDecodeError as err:
            raise EpassError("Token endpoint returned malformed JSON") from err

        token = data.get("access_token")
        if not token:
            raise EpassAuthError("Token endpoint did not return an access token")

        self._access_token = token
        if data.get("refresh_token"):
            self._refresh_token = data["refresh_token"]

        claims = _decode_jwt_payload(token)
        profile = claims.get("UserProfile")
        if isinstance(profile, str):
            try:
                self.user_profile = json.loads(profile)
            except json.JSONDecodeError:
                self.user_profile = {}
        elif isinstance(profile, dict):
            self.user_profile = profile

        expires_in = data.get("expires_in")
        if expires_in:
            self._expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=int(expires_in)
            )
        elif claims.get("exp"):
            self._expires_at = datetime.fromtimestamp(
                int(claims["exp"]), tz=timezone.utc
            )
        else:
            self._expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    async def _async_valid_token(self) -> str:
        async with self._lock:
            if self._access_token is None:
                await self.async_login()
            elif (
                self._expires_at is not None
                and datetime.now(timezone.utc) + TOKEN_LEEWAY >= self._expires_at
            ):
                await self._async_refresh()
            token = self._access_token
        if token is None:
            raise EpassAuthError("No access token available")
        return token

    # --------------------------------------------------------------- request

    async def _async_request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        params: dict[str, Any] | None = None,
        retry: bool = True,
    ) -> Any:
        token = await self._async_valid_token()
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            # The SPA always sends this (a reCAPTCHA token); empty is accepted.
            "gid": "",
        }
        try:
            async with self._session.request(
                method,
                f"{BASE_URL}{path}",
                json=json_body,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                if resp.status in (401, 403):
                    if not retry:
                        raise EpassAuthError("Session rejected by the e-PASS backend")
                    _LOGGER.debug("HTTP %s on %s, renewing session", resp.status, path)
                    async with self._lock:
                        await self._async_refresh()
                    return await self._async_request(
                        method,
                        path,
                        json_body=json_body,
                        params=params,
                        retry=False,
                    )
                resp.raise_for_status()
                text = await resp.text()
                if not text:
                    return None
                return json.loads(text)
        except ClientResponseError as err:
            raise EpassError(f"HTTP {err.status} on {path}") from err
        except (ClientError, asyncio.TimeoutError) as err:
            raise EpassConnectionError(f"Cannot reach {path}: {err}") from err
        except json.JSONDecodeError as err:
            raise EpassError(f"Malformed JSON from {path}") from err

    # ------------------------------------------------------------------ data

    async def async_get_accounts(self) -> list[dict[str, Any]]:
        """All toll accounts linked to this web user."""
        data = await self._async_request("GET", "/api/Account/GetUserAccountsInfo")
        if isinstance(data, dict):
            return [data]
        return data or []

    async def async_get_account(self, account_id: int | str) -> dict[str, Any]:
        """Full account record: balance, billing date, last payment, status."""
        data = await self._async_request("GET", f"/api/Account/GetAccount/{account_id}")
        return data or {}

    async def async_get_billing_dates(
        self, account_id: int | str
    ) -> list[dict[str, Any]]:
        """Past billing periods, newest first.

        Each entry carries ``BillingDateAsDate`` and the statement
        ``IssueNumber``. Note that the sibling GetStatementInfoRecords endpoint
        answers HTTP 500 for this client, so it is deliberately not used.
        """
        data = await self._async_request(
            "GET",
            "/api/Account/GetAccountBillingDateInfo",
            params={"accountId": str(account_id)},
        )
        if isinstance(data, dict):
            return [data]
        return data or []

    async def async_get_transponders(
        self, account_id: int | str
    ) -> list[dict[str, Any]]:
        """Transponders / smartcards together with their vehicle details."""
        data = await self._async_request(
            "GET", f"/api/Account/GetTransponderVehicleInfo/{account_id}"
        )
        if isinstance(data, dict):
            return [data]
        return data or []

    # --------------------------------------------------------------- payments

    async def async_get_stored_cards(self) -> list[dict[str, Any]]:
        """Cards the subscriber has tokenised with the bank.

        Records carry ``Id``, ``Alias``, ``CardNumber`` (last four digits only),
        ``CardTypeId``, ``Token`` and ``ExpiryDate``. No full card number or
        CVV is ever returned -- the token is what a payment reuses.
        """
        data = await self._async_request("GET", STORED_CARDS_PATH)
        if isinstance(data, dict):
            return [data]
        return data or []

    async def async_get_payment_provider_info(self) -> dict[str, Any]:
        """Gateway limits, notably ``MinAmount`` and ``MaxAmount``."""
        data = await self._async_request("GET", PAYMENT_PROVIDER_PATH)
        return data or {}

    async def async_prepare_payment(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Ask the backend to sign a payment order.

        This does NOT move any money. It returns ``Digest``, ``MerchantId``,
        ``OrderId``, ``PostUrl``, ``SuccessUrl`` and ``FailUrl``; the charge
        only happens when those fields are POSTed as a form to ``PostUrl``,
        which is the bank's hosted page and runs 3-D Secure. A browser has to
        make that POST -- it cannot be done from here.
        """
        data = await self._async_request(
            "POST", PAYMENT_PREPARE_PATH, json_body=payload
        )
        return data or {}

    async def async_get_activities(
        self,
        account_id: int | str,
        begin: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        """Account activity between two datetimes, transparently chunked.

        The backend rejects ranges wider than 30 days, so wider requests are
        split and the results concatenated.
        """
        results: list[dict[str, Any]] = []
        chunk_start = begin
        span = timedelta(days=MAX_RANGE_DAYS - 1)
        while chunk_start < end:
            chunk_end = min(chunk_start + span, end)
            payload = {
                "AccountId": int(account_id),
                "BeginLDateTime": _iso_z(chunk_start),
                "EndLDateTime": _iso_z(chunk_end),
                "BeginLDateTimeStr": _js_date_string(chunk_start),
                "EndLDateTimeStr": _js_date_string(chunk_end),
            }
            data = await self._async_request(
                "POST",
                "/api/Account/GetAccountRecentActivities",
                json_body=payload,
            )
            if isinstance(data, list):
                results.extend(data)
            elif isinstance(data, dict):
                results.append(data)
            chunk_start = chunk_end + timedelta(seconds=1)
        return results
