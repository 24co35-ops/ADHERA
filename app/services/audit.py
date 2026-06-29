import logging
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.db.supabase import supabase

logger = logging.getLogger("adhera.audit")

# Dedicated thread-pool for fire-and-forget audit writes
_audit_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="audit")


def _is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError):
        return False


def _do_insert(action: str, user_id: str | None, details: dict):
    """Synchronous insert executed in a background thread."""
    try:
        data = {
            "action_code": action,
            "actor_id": user_id,
            "reason": str(details) if details else None,
        }
        if supabase:
            supabase.table("audit_log").insert(data).execute()
    except Exception as e:
        err = str(e)
        # FK violation: actor_id not yet in profiles (e.g. registration race).
        if "23503" in err or "audit_log_actor_id_fkey" in err:
            logger.warning(
                "Audit insert skipped — actor not yet in profiles. action=%s user=%s",
                action, user_id,
            )
        else:
            logger.error("Failed to log audit action %s for user %s: %s", action, user_id, e)


def log_audit_action(action: str, user_id: str | None, details: dict):
    """
    Fire-and-forget audit log. Runs in a background thread so it never
    delays the HTTP response. Does not raise; silently skips non-UUID actors.
    """
    if user_id is not None and not _is_valid_uuid(user_id):
        logger.debug("Skipping audit log for non-UUID actor_id=%r action=%s", user_id, action)
        return
    try:
        loop = asyncio.get_event_loop()
        loop.run_in_executor(_audit_pool, _do_insert, action, user_id, details)
    except RuntimeError:
        # No running event loop (e.g. during tests) — run synchronously
        _do_insert(action, user_id, details)

