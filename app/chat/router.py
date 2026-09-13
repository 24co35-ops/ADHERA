import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile

from app.auth.dependencies import get_current_user, require_role
from app.chat.engine import rag_engine
from app.chat.schemas import (
    ChatMessageResponse,
    ChatQueryRequest,
    ChatQueryResponse,
    IngestResponse,
)
from app.core.rate_limit import limiter
from app.core.responses import SuccessResponse
from app.core.utils import calculate_age
from app.db.supabase import supabase
from app.services.audit import log_audit_action

logger = logging.getLogger("adhera.chat")
router = APIRouter()


@router.post("/query", response_model=SuccessResponse[ChatQueryResponse])
@limiter.limit("30/minute")
async def query_medical_chat(
    request: Request,
    payload: ChatQueryRequest,
    user: dict = Depends(get_current_user),
):
    """
    Query the grounded clinical assistant.
    For patients: Answers regarding their personal medication routine and clinical safety.
    For providers: Operates strictly within a selected patient's context (adherence, side effects, talking points).
    """
    user_id = user.get("user_id")
    role = user.get("role") or "patient"
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # 1. Resolve and validate target patient ID
    if role == "provider":
        if not payload.patient_id:
            raise HTTPException(
                status_code=400,
                detail="Patient ID is required. The clinical assistant only operates within a selected patient context."
            )
        target_patient_id = payload.patient_id
        # Verify active assignment
        try:
            asg_res = (
                supabase.table("assignments")
                .select("id")
                .eq("provider_id", user_id)
                .eq("patient_id", target_patient_id)
                .eq("status", "active")
                .execute()
            )
            if not asg_res.data:
                raise HTTPException(status_code=403, detail="Not assigned to this patient")
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("Assignment verification failed: %s", str(e))
            raise HTTPException(status_code=403, detail="Unable to verify patient assignment")
    elif role == "admin":
        target_patient_id = payload.patient_id or user_id
    else:
        # Patient role
        if payload.patient_id and payload.patient_id != user_id:
            raise HTTPException(status_code=403, detail="Cannot query another patient's records")
        target_patient_id = user_id

    # 2. Fetch active medicines with full regimen details
    user_medicines: list[dict] = []
    try:
        med_res = (
            supabase.table("medicines")
            .select("id, name, dosage_amount, dosage_unit, route, frequency, frequency_type, instructions, start_date")
            .eq("user_id", target_patient_id)
            .eq("is_active", True)
            .execute()
        )
        user_medicines = med_res.data or []
    except Exception as e:
        logger.warning("Could not fetch medicines for chat context: %s", str(e))

    # 3. Fetch patient profile info
    user_profile: dict = {}
    try:
        prof_res = (
            supabase.table("profiles")
            .select("id, full_name, date_of_birth, blood_group, timezone, medical_conditions, allergies")
            .eq("id", target_patient_id)
            .execute()
        )
        if prof_res.data:
            user_profile = prof_res.data[0]
            user_profile["age"] = calculate_age(user_profile.get("date_of_birth"))
    except Exception as e:
        logger.warning("Could not fetch profile for chat context: %s", str(e))

    # 4. Fetch recent feedback / side-effect logs (last 30 days)
    user_feedback: list[dict] = []
    try:
        d30 = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        fb_res = (
            supabase.table("feedback")
            .select("id, severity, description, medicine_id, created_at, medicines(name)")
            .eq("user_id", target_patient_id)
            .gte("created_at", d30)
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )
        user_feedback = fb_res.data or []
        for fb in user_feedback:
            if isinstance(fb.get("medicines"), dict):
                fb["medicine_name"] = fb["medicines"].get("name")
    except Exception as e:
        logger.warning("Could not fetch feedback for chat context: %s", str(e))

    # 5. Fetch adherence summary (7-day and 30-day rates + streak)
    adherence_summary: dict = {}
    try:
        now = datetime.now(timezone.utc)
        d30_str = (now - timedelta(days=30)).isoformat()
        d7_str = (now - timedelta(days=7)).isoformat()

        adh_res = (
            supabase.table("adherence")
            .select("status, scheduled_utc")
            .eq("user_id", target_patient_id)
            .gte("scheduled_utc", d30_str)
            .order("scheduled_utc", desc=False)
            .execute()
        )
        adh_data = adh_res.data or []

        d7_data = [r for r in adh_data if r.get("scheduled_utc", "") >= d7_str]
        taken_7d = sum(1 for r in d7_data if r.get("status") == "taken")
        missed_7d = sum(1 for r in d7_data if r.get("status") == "missed")
        total_7d = taken_7d + missed_7d
        weekly_rate = round((taken_7d / total_7d) * 100) if total_7d > 0 else None

        taken_30d = sum(1 for r in adh_data if r.get("status") == "taken")
        missed_30d = sum(1 for r in adh_data if r.get("status") == "missed")
        total_30d = taken_30d + missed_30d
        monthly_rate = round((taken_30d / total_30d) * 100) if total_30d > 0 else None

        # Streak calculation
        streak = 0
        for r in reversed(adh_data):
            if r.get("status") == "taken":
                streak += 1
            elif r.get("status") == "missed":
                break

        adherence_summary = {
            "weekly_rate": weekly_rate,
            "monthly_rate": monthly_rate,
            "missed_doses_7d": missed_7d,
            "missed_doses_30d": missed_30d,
            "taken_doses_30d": taken_30d,
            "streak": streak,
        }
    except Exception as e:
        logger.warning("Could not fetch adherence summary for chat context: %s", str(e))

    # 6. Fetch active clinical AI insight flags
    flags_list: list[dict] = []
    try:
        flags_res = (
            supabase.table("patient_flags")
            .select("id, flag_type, severity, details, detected_at")
            .eq("patient_id", target_patient_id)
            .eq("resolved", False)
            .execute()
        )
        flags_list = flags_res.data or []
    except Exception as e:
        logger.debug("Patient flags query skipped: %s", str(e))

    patient_context = {
        "medicines": user_medicines,
        "profile": user_profile,
        "recent_feedback": user_feedback,
        "adherence_summary": adherence_summary,
        "flags": flags_list,
    }

    # Process query through RAG Engine with role-appropriate mode
    is_provider = (role == "provider")
    answer, citations, suggested_feedback = rag_engine.process_query(
        query=payload.message,
        user_medicines=user_medicines,
        patient_context=patient_context,
        is_provider=is_provider,
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    response_id = str(uuid.uuid4())

    # Audit log for provider interactions
    if is_provider:
        log_audit_action("PROVIDER_AI_CONSULTATION", user_id, {
            "patient_id": target_patient_id,
            "query_preview": payload.message[:100],
        })

    # Record interaction to chat_messages table
    try:
        supabase.table("chat_messages").insert({
            "user_id": user_id,
            "role": "user",
            "content": payload.message,
            "created_at": now_iso
        }).execute()

        supabase.table("chat_messages").insert({
            "id": response_id,
            "user_id": user_id,
            "role": "assistant",
            "content": answer,
            "sources": [s.model_dump() for s in citations],
            "suggested_feedback": suggested_feedback.model_dump() if suggested_feedback else None,
            "created_at": now_iso
        }).execute()
    except Exception as e:
        logger.warning("Could not persist chat messages to database: %s", str(e))

    return SuccessResponse(data=ChatQueryResponse(
        id=response_id,
        role="assistant",
        content=answer,
        sources=citations,
        suggested_feedback=suggested_feedback,
        created_at=now_iso
    ))


@router.get("/history", response_model=SuccessResponse[List[ChatMessageResponse]])
@limiter.limit("60/minute")
async def get_chat_history(
    request: Request,
    patient_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    """Retrieve chat message history for the authenticated user."""
    user_id = user.get("user_id")
    role = user.get("role") or "patient"
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    if role == "provider" and patient_id:
        # Check assignment
        asg = supabase.table("assignments").select("id").eq("provider_id", user_id).eq("patient_id", patient_id).eq("status", "active").execute()
        if not asg.data:
            raise HTTPException(status_code=403, detail="Not assigned to this patient")

    try:
        res = (
            supabase.table("chat_messages")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .limit(50)
            .execute()
        )
        data = res.data or []
    except Exception as e:
        logger.warning("Could not fetch chat history: %s", str(e))
        data = []

    return SuccessResponse(data=data)


@router.post("/ingest", response_model=SuccessResponse[IngestResponse])
@limiter.limit("10/minute")
async def ingest_medical_documents(
    request: Request,
    file: Optional[UploadFile] = File(None),
    user: dict = Depends(require_role("admin")),
):
    """
    Admin-only endpoint to ingest / refresh medical reference guidelines into the RAG vector index.
    """
    kb_dir = rag_engine.kb_dir
    os.makedirs(kb_dir, exist_ok=True)

    if file and file.filename:
        # Save uploaded file
        clean_filename = os.path.basename(file.filename)
        dest_path = os.path.join(kb_dir, clean_filename)
        content = await file.read()
        with open(dest_path, "wb") as f:
            f.write(content)

    doc_count, chunk_count = rag_engine.ingest_seed_documents()

    return SuccessResponse(data=IngestResponse(
        documents_ingested=doc_count,
        chunks_created=chunk_count,
        status="Index refreshed successfully"
    ))
