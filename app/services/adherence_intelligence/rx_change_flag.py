"""Prescription change signal detector — flags suspicious medication edit patterns."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.db.supabase import supabase

logger = logging.getLogger(__name__)


async def detect_rx_change_flags(patient_id: str, lookback_days: int = 30) -> dict:
    """Detect prescription change signals from the medicines table.

    Flags raised:
      rapid_edit       — same medication updated ≥2 times in 30 days
                         (detected as updated_at ≠ created_at within window)
      rapid_replacement — a medication became inactive AND a new one was created within 7 days
      early_change     — updated_at within 14 days of created_at
      multiple_active  — ≥3 medications currently active
    """
    res = await asyncio.to_thread(
        lambda: supabase.table("medicines")
        .select("id, name, is_active, created_at, updated_at")
        .eq("user_id", patient_id)
        .execute()
    )
    meds = res.data or []

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=lookback_days)
    flags: list[dict] = []

    active_meds = [m for m in meds if m.get("is_active")]
    inactive_meds = [m for m in meds if not m.get("is_active")]

    # Flag: multiple_active
    if len(active_meds) >= 3:
        flags.append({
            "type": "multiple_active",
            "medication_name": ", ".join(m["name"] for m in active_meds),
            "description": f"Patient has {len(active_meds)} active medications — verify intentional polypharmacy.",
            "active_count": len(active_meds),
        })

    for med in meds:
        created = datetime.fromisoformat(med["created_at"].replace("Z", "+00:00"))
        updated = datetime.fromisoformat(med["updated_at"].replace("Z", "+00:00"))

        # Flag: rapid_edit (updated within window and updated ≠ created)
        if updated > cutoff and (updated - created).total_seconds() > 60:
            flags.append({
                "type": "rapid_edit",
                "medication_name": med["name"],
                "description": f"{med['name']} was modified {(now - updated).days} days ago, within {lookback_days} days of creation or last edit.",
                "days_since_edit": (now - updated).days,
            })

        # Flag: early_change (updated within 14 days of creation)
        if (updated - created).days < 14 and (updated - created).total_seconds() > 60:
            flags.append({
                "type": "early_change",
                "medication_name": med["name"],
                "description": f"{med['name']} was changed only {(updated - created).days} days after being prescribed.",
                "days_between": (updated - created).days,
            })

    # Flag: rapid_replacement — inactive med + new active med within 7 days
    for inact in inactive_meds:
        inact_updated = datetime.fromisoformat(inact["updated_at"].replace("Z", "+00:00"))
        for act in active_meds:
            act_created = datetime.fromisoformat(act["created_at"].replace("Z", "+00:00"))
            gap = abs((act_created - inact_updated).days)
            if gap <= 7 and act_created >= inact_updated:
                flags.append({
                    "type": "rapid_replacement",
                    "medication_name": f"{inact['name']} → {act['name']}",
                    "description": f"{inact['name']} was discontinued and replaced by {act['name']} within {gap} days.",
                    "days_between": gap,
                })

    # Deduplicate by (type, medication_name)
    seen: set[tuple] = set()
    unique_flags = []
    for f in flags:
        key = (f["type"], f["medication_name"])
        if key not in seen:
            seen.add(key)
            unique_flags.append(f)

    flag_raised = len(unique_flags) > 0
    clinical_note: str | None = None
    if flag_raised:
        types = list({f["type"] for f in unique_flags})
        clinical_note = f"Prescription change signals detected: {', '.join(types)}. Clinical review recommended."

    return {
        "flag_raised": flag_raised,
        "flags": unique_flags,
        "clinical_note": clinical_note,
    }
