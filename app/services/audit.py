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


def log_audit_action(action: str, user_id: str | None, details: dict):
    """
    Log an audit action to the database.
    Does not raise exceptions if logging fails to prevent breaking the main flow.
    Skips insert silently if user_id is not a valid UUID (e.g. test mocks).
    """
    if user_id is not None and not _is_valid_uuid(user_id):
        logger.debug("Skipping audit log for non-UUID actor_id=%r action=%s", user_id, action)
        return
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
        # Log as warning — not an actionable error, just a timing artifact.
        if "23503" in err or "audit_log_actor_id_fkey" in err:
            logger.warning(
                "Audit insert skipped — actor not yet in profiles. action=%s user=%s",
                action, user_id,
            )
        else:
            logger.error("Failed to log audit action %s for user %s: %s", action, user_id, e)
