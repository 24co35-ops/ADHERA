import logging
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

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
from app.db.supabase import supabase

logger = logging.getLogger("adhera.chat")
router = APIRouter()


@router.post("/query", response_model=SuccessResponse[ChatQueryResponse])
@limiter.limit("20/hour")
async def query_medical_chat(
    request: Request,
    payload: ChatQueryRequest,
    user: dict = Depends(get_current_user),
):
    """
    Query the grounded medical knowledge assistant.
    Answers strictly from verified clinical references and checks for side-effects.
    """
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Fetch active user medicines to correlate side effects
    user_medicines: list[dict] = []
    try:
        med_res = (
            supabase.table("medicines")
            .select("id, name, dosage_amount, dosage_unit")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .execute()
        )
        user_medicines = med_res.data or []
    except Exception as e:
        logger.warning("Could not fetch user medicines for chat context: %s", str(e))

    # Process query through RAG Engine
    answer, citations, suggested_feedback = rag_engine.process_query(
        query=payload.message,
        user_medicines=user_medicines
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    response_id = str(uuid.uuid4())

    # Record interaction to chat_messages table
    try:
        # Save user message
        supabase.table("chat_messages").insert({
            "user_id": user_id,
            "role": "user",
            "content": payload.message,
            "created_at": now_iso
        }).execute()

        # Save assistant message
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
    user: dict = Depends(get_current_user),
):
    """Retrieve chat message history for the authenticated user."""
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

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
