"""Intelligence router — single unified endpoint for adherence intelligence."""
import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth.dependencies import require_role
from app.core.rate_limit import limiter
from app.core.responses import SuccessResponse
from app.db.supabase import supabase
from app.services.adherence_intelligence.confidence import compute_confidence
from app.services.adherence_intelligence.fusion_engine import compute_risk_score
from app.services.adherence_intelligence.pattern_classifier import (
    classify_adherence_pattern,
)
from app.services.adherence_intelligence.rx_change_flag import detect_rx_change_flags

router = APIRouter()
logger = logging.getLogger(__name__)


def _build_summary(risk: dict, confidence: dict, pattern: dict) -> str:
    risk_level = risk["risk_level"].capitalize()
    conf_label = confidence["confidence_label"].lower()
    ptype = pattern["pattern_type"].replace("_", " ")
    return (
        f"{risk_level} adherence risk detected with {conf_label} confidence"
        f" — patient shows {ptype} pattern."
    )


@router.get("/intelligence/{patient_id}", response_model=SuccessResponse[dict])
@limiter.limit("30/minute")
async def get_patient_intelligence(
    request: Request,
    patient_id: str,
    user: dict = Depends(require_role("provider", "admin")),
):
    """Return full adherence intelligence for a patient in one call.

    Runs risk score, confidence, pattern classification, and Rx flags concurrently.
    Only providers assigned to the patient or admins may call this endpoint.
    """
    # 404 guard: check patient exists
    profile = await asyncio.to_thread(
        lambda: supabase.table("profiles").select("id, role").eq("id", patient_id).limit(1).execute()
    )
    if not profile.data:
        raise HTTPException(status_code=404, detail="Patient not found")

    if profile.data[0].get("role") != "patient":
        raise HTTPException(status_code=400, detail="Requested ID is not a patient")

    # Providers must be assigned to the patient
    if user["role"] == "provider":
        asg = await asyncio.to_thread(
            lambda: supabase.table("assignments")
            .select("id")
            .eq("provider_id", user["user_id"])
            .eq("patient_id", patient_id)
            .eq("status", "active")
            .execute()
        )
        if not asg.data:
            raise HTTPException(status_code=403, detail="Not assigned to this patient")

    risk, confidence, pattern, rx_flags = await asyncio.gather(
        compute_risk_score(patient_id),
        compute_confidence(patient_id),
        classify_adherence_pattern(patient_id),
        detect_rx_change_flags(patient_id),
    )

    return SuccessResponse(data={
        "patient_id": patient_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "risk": risk,
        "confidence": confidence,
        "pattern": pattern,
        "rx_flags": rx_flags,
        "summary": _build_summary(risk, confidence, pattern),
    })
