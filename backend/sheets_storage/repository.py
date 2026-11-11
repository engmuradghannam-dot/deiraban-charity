"""Google Sheets-backed domain repository with an offline fake for tests.

Authentication/session data remains in Django. This module only stores domain rows.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

TAB_HEADERS = {
    "members": ["id", "user_id", "membership_number", "full_name", "family_name", "phone", "membership_type", "status", "created_at"],
    "donations": ["id", "campaign_id", "member_id", "user_id", "donor_name", "donor_phone", "amount", "currency", "method", "status", "notes", "created_at"],
    "elections": ["id", "title", "description", "max_choices", "starts_at", "ends_at", "is_active", "results_public", "created_at", "candidates_json"],
    "votes": ["id", "election_id", "voter_id", "submitted_at", "candidate_ids_json"],
    "campaigns": ["id", "title", "description", "goal_amount", "is_active", "created_at"],
}


def _string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    return str(value)


def _bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def normalize_name(value: Any) -> str:
    import re
    import unicodedata
    value = unicodedata.normalize("NFKC", str(value or "")).replace("ـ", "")
    value = re.sub(r"[\u064B-\u065F\u0670]", "", value)
    return " ".join(value.casefold().split())


class InMemorySheetsClient:
    """A deterministic Sheets-like client used by unit tests; never performs I/O."""
    def __init__(self, rows: dict[str, list[dict[str, Any]]] | None = None):
        self.rows = {tab: list(values) for tab, values in (rows or {}).items()}

    def read_rows(self, tab: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.rows.get(tab, [])]

    def append_row(self, tab: str, row: dict[str, Any]) -> dict[str, Any]:
        self.rows.setdefault(tab, []).append(dict(row))
        return dict(row)

    def update_row_by_id(self, tab: str, row_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        for row in self.rows.get(tab, []):
            if str(row.get("id", "")) == str(row_id):
                row.update(updates)
                return dict(row)
        return None


class GoogleSheetsClient:
    """Small adapter around Sheets API v4. Imports are lazy so disabled deployments need no credentials."""
    def __init__(self, spreadsheet_id: str | None = None, credentials_json: str | None = None, service: Any = None):
        self.spreadsheet_id = spreadsheet_id or os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip()
        self.credentials_json = credentials_json or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
        if not self.spreadsheet_id or not self.credentials_json:
            raise RuntimeError("SHEETS_STORAGE_ENABLED requires GOOGLE_SERVICE_ACCOUNT_JSON and GOOGLE_SHEETS_SPREADSHEET_ID")
        if service is not None:
            self.service = service
        else:
            try:
                from google.oauth2.service_account import Credentials
                from googleapiclient.discovery import build
            except ImportError as exc:
                raise RuntimeError("Install google-auth and google-api-python-client for Sheets storage") from exc
            info = json.loads(self.credentials_json)
            credentials = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
            self.service = build("sheets", "v4", credentials=credentials, cache_discovery=False)

    def read_rows(self, tab: str) -> list[dict[str, Any]]:
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id, range=f"'{tab}'!A:Z"
        ).execute()
        values = result.get("values", [])
        if not values:
            return []
        headers = values[0]
        return [dict(zip(headers, row + [""] * (len(headers) - len(row)))) for row in values[1:]]

    def append_row(self, tab: str, row: dict[str, Any]) -> dict[str, Any]:
        headers = TAB_HEADERS[tab]
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"'{tab}'!A:A",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [[_string(row.get(header, "")) for header in headers]]},
        ).execute()
        return row

    def update_row_by_id(self, tab: str, row_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        rows = self.read_rows(tab)
        headers = TAB_HEADERS[tab]
        for index, row in enumerate(rows, start=2):
            if str(row.get("id", "")) != str(row_id):
                continue
            merged = {**row, **updates}
            last_column = chr(64 + len(headers))
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{tab}'!A{index}:{last_column}{index}",
                valueInputOption="USER_ENTERED",
                body={"values": [[_string(merged.get(header, "")) for header in headers]]},
            ).execute()
            return merged
        return None


class SheetsRepository:
    def __init__(self, client: Any | None = None):
        self.client = client or GoogleSheetsClient()

    def _rows(self, tab: str) -> list[dict[str, Any]]:
        return self.client.read_rows(tab)

    def _member_tab(self) -> str:
        configured = os.getenv("GOOGLE_SHEETS_MEMBERS_TAB", "الأعضاء").strip() or "الأعضاء"
        if hasattr(self.client, "rows") and configured not in self.client.rows and "members" in self.client.rows:
            return "members"
        return configured

    def _member_rows(self) -> list[dict[str, Any]]:
        return self._rows(self._member_tab())

    @staticmethod
    def _member_view(row: dict[str, Any]) -> dict[str, Any]:
        """Support the existing sheet columns: number, name, family."""
        return {
            **row,
            "id": row.get("id") or row.get("number", ""),
            "membership_number": row.get("membership_number") or row.get("number", ""),
            "full_name": row.get("full_name") or row.get("name", ""),
            "family_name": row.get("family_name") or row.get("family", ""),
            "membership_type": row.get("membership_type") or row.get("status", "inactive"),
        }

    def campaigns(self) -> list[dict[str, Any]]:
        campaigns = []
        donations = self._rows("donations")
        for row in self._rows("campaigns"):
            if not _bool(row.get("is_active")):
                continue
            completed = sum(Decimal(str(d.get("amount") or "0")) for d in donations if d.get("campaign_id") == row.get("id") and d.get("status") == "completed")
            goal = Decimal(str(row["goal_amount"])) if row.get("goal_amount") else None
            campaigns.append({**row, "collected": completed, "goal_amount": goal, "percent": round(float(completed / goal * 100), 1) if goal else None})
        return campaigns

    def member_for_user(self, user_id: Any) -> dict[str, Any] | None:
        return next((self._member_view(r) for r in self._member_rows() if r.get("user_id") == _string(user_id)), None)

    def member_for_name(self, full_name: str, family_name: str) -> dict[str, Any] | None:
        wanted_full_name = normalize_name(full_name)
        wanted_family_name = normalize_name(family_name)
        return next(
            (
                self._member_view(r) for r in self._member_rows()
                if normalize_name(r.get("full_name") or r.get("name")) == wanted_full_name
                and normalize_name(r.get("family_name") or r.get("family")) == wanted_family_name
            ),
            None,
        )

    def member_application_for_name(self, full_name: str, family_name: str) -> dict[str, Any] | None:
        wanted_full_name = normalize_name(full_name)
        wanted_family_name = normalize_name(family_name)
        return next(
            (
                row for row in self._rows("members")
                if normalize_name(row.get("full_name")) == wanted_full_name
                and normalize_name(row.get("family_name")) == wanted_family_name
            ),
            None,
        )

    def member_for_credentials(self, full_name: str, membership_number: str) -> dict[str, Any] | None:
        wanted_name = normalize_name(full_name)
        wanted_number = str(membership_number or "").strip().casefold()
        return next(
            (
                self._member_view(r) for r in self._member_rows()
                if (
                    normalize_name(r.get("full_name") or r.get("name")) == wanted_name
                    or normalize_name(
                        f"{r.get('full_name') or r.get('name', '')} {r.get('family_name') or r.get('family', '')}"
                    ) == wanted_name
                )
                and str(r.get("membership_number") or r.get("number", "")).strip().casefold() == wanted_number
            ),
            None,
        )

    def member_for_id(self, member_id: Any) -> dict[str, Any] | None:
        return next((self._member_view(r) for r in self._member_rows() if str(r.get("id") or r.get("number", "")) == str(member_id)), None)

    def link_member_to_user(self, member_id: Any, user_id: Any, phone: str = "") -> dict[str, Any] | None:
        row = self.member_for_id(member_id)
        if not row:
            return None
        updates = {"user_id": _string(user_id)}
        if phone and not row.get("phone"):
            updates["phone"] = phone
        # The legacy Arabic tab has no id/user_id columns. Authentication uses
        # the stable membership number, so do not try to rewrite that source tab.
        raw_row = next(
            (item for item in self._member_rows() if str(item.get("id") or item.get("number", "")) == str(member_id)),
            None,
        )
        if raw_row is not None and "user_id" not in raw_row and "id" not in raw_row:
            row.update(updates)
            return row
        updater = getattr(self.client, "update_row_by_id", None)
        if updater:
            return updater(self._member_tab(), str(member_id), updates)
        row.update(updates)
        return row

    def create_member(self, data: dict[str, Any]) -> dict[str, Any]:
        row = {"id": uuid.uuid4().hex, "created_at": datetime.now(UTC).isoformat(), "status": "pending", **data}
        return self.client.append_row(self._member_tab(), row)

    def create_member_application(self, data: dict[str, Any]) -> dict[str, Any]:
        """Store a public registration request without assigning a membership number."""
        row = {
            "id": uuid.uuid4().hex,
            "user_id": "",
            "membership_number": "",
            "membership_type": "inactive",
            "status": "pending",
            "created_at": datetime.now(UTC).isoformat(),
            **data,
        }
        # The English members tab is retained as the review queue. Verified
        # members remain in the Arabic الأعضاء tab and are never overwritten.
        return self.client.append_row("members", row)

    def create_donation(self, data: dict[str, Any]) -> dict[str, Any]:
        row = {"id": uuid.uuid4().hex, "created_at": datetime.now(UTC).isoformat(), "currency": "JOD", "status": "pending", **data}
        return self.client.append_row("donations", row)

    def donations_for_user(self, user_id: Any, member_id: Any = None) -> list[dict[str, Any]]:
        return [r for r in self._rows("donations") if r.get("user_id") == _string(user_id) or (member_id is not None and r.get("member_id") == _string(member_id))]

    def elections(self) -> list[dict[str, Any]]:
        return self._with_candidates(self._rows("elections"))

    def election(self, election_id: Any) -> dict[str, Any] | None:
        return next((r for r in self.elections() if r.get("id") == _string(election_id)), None)

    def _with_candidates(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for row in rows:
            raw = row.get("candidates_json", "[]")
            try: row["candidates"] = json.loads(raw) if isinstance(raw, str) else raw
            except (TypeError, ValueError): row["candidates"] = []
        return rows

    def has_voted(self, election_id: Any, voter_id: Any) -> bool:
        return any(r.get("election_id") == _string(election_id) and r.get("voter_id") == _string(voter_id) for r in self._rows("votes"))

    def record_vote(self, election_id: Any, voter_id: Any, candidate_ids: list[Any]) -> dict[str, Any]:
        if self.has_voted(election_id, voter_id):
            raise ValueError("duplicate_vote")
        row = {"id": uuid.uuid4().hex, "election_id": _string(election_id), "voter_id": _string(voter_id), "submitted_at": datetime.now(UTC).isoformat(), "candidate_ids_json": json.dumps([_string(i) for i in candidate_ids])}
        return self.client.append_row("votes", row)

    def results(self, election_id: Any) -> tuple[list[dict[str, Any]], int, int]:
        election_id = _string(election_id)
        rows = [r for r in self._rows("votes") if r.get("election_id") == election_id]
        counts: dict[str, int] = {}
        for row in rows:
            try: ids = json.loads(row.get("candidate_ids_json", "[]"))
            except (TypeError, ValueError): ids = []
            for cid in ids: counts[_string(cid)] = counts.get(_string(cid), 0) + 1
        election = self.election(election_id) or {}
        candidates = election.get("candidates", [])
        result = [{**candidate, "votes": counts.get(_string(candidate.get("id")), 0)} for candidate in candidates]
        result.sort(key=lambda r: (-r["votes"], r.get("name", "")))
        return result, len(rows), sum(counts.values())


def sheets_enabled() -> bool:
    return os.getenv("SHEETS_STORAGE_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
