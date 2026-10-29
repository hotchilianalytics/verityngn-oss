"""Server-side locks (SplitRisk concept section 2.2).

Outside hosts never render our UI, so every lock is enforced here and every
rejection names an allowed alternative the model can relay to the user.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Iterable, Optional

from verityngn.agent.mcp_v2.errors import ToolFailure

MAX_WINDOW_DAYS = 366

SCHEDULE_KEYS = frozenset(
    {
        "schedule",
        "cron",
        "recurring",
        "recurrence",
        "repeat",
        "interval",
        "every",
        "monitor",
        "alert",
        "alerts",
        "watch",
        "subscribe",
        "notify",
    }
)

DECIDE_ACTIONS = frozenset({"accept", "edit", "reject", "set_judgment", "clear_judgment"})
CONFIRMATION_EXEMPT = frozenset({"resolve_entity"})


def today() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).date()


def parse_date(value: str, field: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ToolFailure("INVALID", f"{field} must be an ISO date (YYYY-MM-DD), got {value!r}") from None


def check_window(window: dict[str, str], *, now: Optional[dt.date] = None) -> tuple[dt.date, dt.date]:
    """Reject windows longer than 366 days or ending in the future."""
    now = now or today()
    start = parse_date(window.get("from", ""), "window.from")
    end = parse_date(window.get("to", ""), "window.to")
    if start > end:
        raise ToolFailure("INVALID", "window.from is after window.to")
    if end > now:
        raise ToolFailure(
            "LOCK_WINDOW",
            f"Windows cannot end in the future (to={end.isoformat()}, today={now.isoformat()}). "
            "Nothing is scheduled or monitored.",
            alternative=f"Run the same query for a window ending today: from {max(start, now - dt.timedelta(days=MAX_WINDOW_DAYS)).isoformat()} to {now.isoformat()}. "
            "To repeat it later, save the query and re-run it.",
        )
    if (end - start).days > MAX_WINDOW_DAYS:
        raise ToolFailure(
            "LOCK_WINDOW",
            f"Windows are limited to {MAX_WINDOW_DAYS} days; this one is {(end - start).days} days.",
            alternative=f"Narrow the window to at most {MAX_WINDOW_DAYS} days, for example "
            f"from {(end - dt.timedelta(days=MAX_WINDOW_DAYS)).isoformat()} to {end.isoformat()}.",
        )
    return start, end


def window_dict(start: dt.date, end: dt.date) -> dict[str, str]:
    return {"from": start.isoformat(), "to": end.isoformat()}


def preset_window(preset: str, *, now: Optional[dt.date] = None, last_10k: Optional[dt.date] = None) -> dict[str, str]:
    now = now or today()
    if preset == "last_reported_quarter":
        q_start_month = 3 * ((now.month - 1) // 3) + 1
        this_q = dt.date(now.year, q_start_month, 1)
        end = this_q - dt.timedelta(days=1)
        start = dt.date(end.year, 3 * ((end.month - 1) // 3) + 1, 1)
        return window_dict(start, end)
    if preset == "since_last_10k":
        if last_10k is None:
            raise ToolFailure(
                "NOT_FOUND",
                "No 10-K found for this issuer in the last year, so 'since_last_10k' cannot be resolved.",
                alternative="Use the last_90_days preset or pass an explicit window.",
            )
        start = max(last_10k, now - dt.timedelta(days=MAX_WINDOW_DAYS))
        return window_dict(start, now)
    return window_dict(now - dt.timedelta(days=90), now)


def reject_schedule_arguments(arguments: dict[str, Any]) -> None:
    hits = sorted(k for k in arguments if k.lower() in SCHEDULE_KEYS)
    if hits:
        raise ToolFailure(
            "INVALID",
            f"No tool accepts a schedule, alert or monitor ({', '.join(hits)}). Every query is a one-off user request.",
            alternative="Save the query so you can re-run it yourself, or draft a written monitor plan for the issuer to approve.",
        )


def require_channel_owned(channel_id: str, owned: Iterable[dict[str, Any]], entity_name: str) -> None:
    owned_ids = [c.get("channel_id") for c in owned]
    if channel_id not in owned_ids:
        listing = ", ".join(i for i in owned_ids if i) or "none verified yet"
        raise ToolFailure(
            "LOCK_CHANNEL_NOT_OWNED",
            f"Only channels {entity_name} owns can be listed; {channel_id} is not on its verified owned-channel list.",
            alternative=f"List one of the owned channels ({listing}), or upload a video you already have rights to "
            "with register_document and assess it.",
        )


def require_decide_role(role: str, action: str) -> None:
    if action in DECIDE_ACTIONS and role != "gc":
        raise ToolFailure(
            "LOCK_ROLE",
            f"'{action}' is a general counsel decision; the {role} role can only propose.",
            alternative="Call record_review_action with action 'propose' and a note; general counsel will decide.",
        )


def require_licence(licences: Iterable[str], licence: str, what: str) -> None:
    if licence not in set(licences):
        raise ToolFailure(
            "LOCK_NO_LICENCE",
            f"{what} needs the '{licence}' licence on file for this tenant.",
            alternative="Use filings_search for the issuer's own litigation disclosures (10-K Item 3, 8-K) until the licence is signed.",
        )


def needs_confirmation(tool: str, role: str, arguments: dict[str, Any], resolved: dict[str, Any]) -> None:
    if role != "junior" or tool in CONFIRMATION_EXEMPT or arguments.get("confirmed") is True:
        return
    raise ToolFailure(
        "NEEDS_CONFIRMATION",
        "Junior searches run only after you confirm the entity and window.",
        alternative="Check the resolved entity and window below, then repeat the same call with confirmed: true.",
        details=resolved,
    )
