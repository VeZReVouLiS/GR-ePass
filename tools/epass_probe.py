#!/usr/bin/env python3
"""Standalone probe for the my e-PASS web API (Attiki Odos).

Run it on your own machine with your own credentials to see exactly what the
backend returns. Nothing is uploaded anywhere; the output is written next to
this script. Use it to confirm the integration reads the right fields, or to
share a redacted sample when something looks wrong.

    python epass_probe.py YOUR_USERNAME
    python epass_probe.py YOUR_USERNAME --days 14 --out sample.json
    python epass_probe.py YOUR_USERNAME --no-redact      # full, personal data

The password is read from the terminal (never echoed) or from the EPASS_PASSWORD
environment variable. Only stdlib is used, so no pip install is needed.
"""

from __future__ import annotations

import argparse
import base64
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

BASE_URL = "https://epass.naodos.gr"
CLIENT_ID = "100"
CLIENT_SECRET = "secret"
MAX_RANGE_DAYS = 30

REDACT_KEYS = {
    "AltEmail",
    "AlternatePhone",
    "Answer",
    "BankAccountFirstName",
    "BankAccountLastName",
    "BankAccountName",
    "BankAccountNumber",
    "BankTransitNumber",
    "BillingAddress",
    "BillingCity",
    "BillingPostalCode",
    "ContactPersonFirstName",
    "ContactPersonLastName",
    "Email",
    "FatherFirstName",
    "FatherLastName",
    "Fax",
    "FirstName",
    "LastName",
    "MailingAddress",
    "MailingCity",
    "MailingPostalCode",
    "MobilePhone",
    "NationalInsNumber",
    "Password",
    "PaymentNumber",
    "PlateNum",
    "PreAuthCardHolder",
    "PreAuthCardNumber",
    "PrimaryPhone",
    "Question",
    "Sms",
    "TaxFiscalId",
    "UserLogonId",
    "UserName",
}


def redact(value: Any) -> Any:
    """Replace personal values with a placeholder, recursively."""
    if isinstance(value, dict):
        return {
            key: ("<redacted>" if key in REDACT_KEYS and item else redact(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def post_form(path: str, payload: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=urlencode(payload).encode(),
        headers={
            "Content-Type": "x-www-form-urlencoded",
            "Audience": "Any",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as err:
        body = err.read().decode(errors="replace")
        raise SystemExit(f"Login failed (HTTP {err.code}): {body}") from err


def api(path: str, token: str, body: Any | None = None) -> Any:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "gid": "",
        },
        method="POST" if data is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as err:
        return {
            "__error__": err.code,
            "__body__": err.read().decode(errors="replace")[:2000],
            "__path__": path,
        }


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def jwt_claims(token: str) -> dict[str, Any]:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:  # noqa: BLE001 - best effort only
        return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username")
    parser.add_argument(
        "--days", type=int, default=7, help="how many days of activity to pull"
    )
    parser.add_argument("--out", default="epass_probe_output.json")
    parser.add_argument(
        "--no-redact",
        action="store_true",
        help="keep names, plates, emails and tax ids in the output",
    )
    args = parser.parse_args()

    password = os.environ.get("EPASS_PASSWORD") or getpass.getpass(
        "my e-PASS password: "
    )

    print("-> logging in ...")
    tokens = post_form(
        "/oauth2/token",
        {
            "username": args.username,
            "password": password,
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "stay_signed_in": "true",
        },
    )
    token = tokens.get("access_token")
    if not token:
        raise SystemExit(f"No access token in response: {tokens}")
    claims = jwt_claims(token)
    print(
        f"   ok, token expires in {tokens.get('expires_in')}s, "
        f"refresh token: {'yes' if tokens.get('refresh_token') else 'no'}"
    )

    result: dict[str, Any] = {
        "token_response_keys": sorted(tokens),
        "jwt_claim_keys": sorted(claims),
        "accounts": [],
    }

    print("-> GET /api/Account/GetUserAccountsInfo")
    accounts = api("/api/Account/GetUserAccountsInfo", token) or []
    if isinstance(accounts, dict):
        accounts = [accounts]
    result["user_accounts"] = accounts
    print(f"   {len(accounts)} account(s)")

    end = datetime.now(timezone.utc).astimezone() + timedelta(days=1)
    begin = end - timedelta(days=min(args.days, MAX_RANGE_DAYS - 1))

    for account in accounts:
        account_id = (
            account.get("AccountID")
            or account.get("AccountId")
            or account.get("accountId")
        )
        if account_id is None:
            continue
        print(f"-> account {account_id}: detail, transponders, activity")
        entry = {
            "account_id": account_id,
            "detail": api(f"/api/Account/GetAccount/{account_id}", token),
            "transponders": api(
                f"/api/Account/GetTransponderVehicleInfo/{account_id}", token
            ),
            "billing_date_info": api(
                f"/api/Account/GetAccountBillingDateInfo?accountId={account_id}",
                token,
            ),
            "statement_info_records": api(
                f"/api/Account/GetStatementInfoRecords?accountId={account_id}",
                token,
            ),
            "activities": api(
                "/api/Account/GetAccountRecentActivities",
                token,
                {
                    "AccountId": int(account_id),
                    "BeginLDateTime": iso_z(begin),
                    "EndLDateTime": iso_z(end),
                    "BeginLDateTimeStr": begin.strftime("%a %b %d %Y %H:%M:%S"),
                    "EndLDateTimeStr": end.strftime("%a %b %d %Y %H:%M:%S"),
                },
            ),
        }
        activities = entry["activities"]
        if isinstance(activities, list):
            print(f"   {len(activities)} activity record(s) in the last {args.days}d")
            if activities:
                print(f"   fields: {', '.join(sorted(activities[0]))}")
        result["accounts"].append(entry)

    payload = result if args.no_redact else redact(result)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, default=str)
    print(f"\nWrote {args.out}")
    if not args.no_redact:
        print("Personal fields were replaced with <redacted>.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
