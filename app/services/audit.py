import logging
from app.db.supabase import supabase

logger = logging.getLogger("adhera.audit")

def log_audit_action(action: str, user_id: str | None, details: dict):
    """
    Log an audit action to the database.
    Does not raise exceptions if logging fails to prevent breaking the main flow.
    """
    try:
        data = {
            "action_code": action,
            "actor_id": user_id,
            "reason": str(details) if details else None,
        }
        if supabase:
            supabase.table("audit_log").insert(data).execute()
    except Exception as e:
        logger.error(f"Failed to log audit action {action} for user {user_id}: {e}")
