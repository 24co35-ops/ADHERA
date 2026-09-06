import asyncio
import logging
import uuid

from app.db.supabase import supabase

logger = logging.getLogger("adhera.audit")


def _is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError):
        return False


def _do_insert(action: str, user_id: str | None, details: dict):
    """Synchronous insert executed in a background thread with retry on transient network errors."""
    if not supabase:
        return

    data = {
        "action_code": action,
        "actor_id": user_id,
        "reason": str(details) if details else None,
    }

    for attempt in range(2):
        try:
            supabase.table("audit_log").insert(data).execute()
            return
        except Exception as e:
            err = str(e)
            # FK violation: actor_id not yet in profiles (e.g. registration race).
            if "23503" in err or "audit_log_actor_id_fkey" in err:
                logger.warning(
                    "Audit insert skipped — actor not yet in profiles. action=%s user=%s",
                    action, user_id,
                )
                return

            is_transient = any(
                sub in err.lower()
                for sub in ["ssl", "eof", "connection", "timeout", "protocol", "reset", "broken pipe"]
            )
            if attempt == 0 and is_transient:
                continue

            logger.warning("Failed to log audit action %s for user %s: %s", action, user_id, e)
            return


def log_audit_action(action: str, user_id: str | None, details: dict):
    """
    Fire-and-forget audit log. Dispatches to asyncio.to_thread when an event loop is running.
    Does not raise; silently skips non-UUID actors.
    """
    if user_id is not None and not _is_valid_uuid(user_id):
        logger.debug("Skipping audit log for non-UUID actor_id=%r action=%s", user_id, action)
        return
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(asyncio.to_thread(_do_insert, action, user_id, details))
    except RuntimeError:
        # No running event loop (e.g. during tests) — run synchronously
        _do_insert(action, user_id, details)


