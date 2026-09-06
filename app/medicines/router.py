from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.db.supabase import supabase

supabase = supabase
from app.auth.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.core.responses import SuccessResponse
from app.medicines.schemas import MedicineCreate, MedicineUpdate
from app.services.audit import log_audit_action

router = APIRouter()

def _check_assignment(provider_id: str, patient_id: str):
    """Verify provider is assigned to patient. Raises 403 if not."""
    res = supabase.table("assignments").select("id").eq("provider_id", provider_id).eq("patient_id", patient_id).eq("status", "active").execute()
    if not res.data:
        raise HTTPException(status_code=403, detail="Not assigned to this patient")

def _resolve_user_id(user: dict, patient_id: str = None):
    """Resolve the target user_id based on role and patient_id param."""
    role = user.get("role", "patient")
    if role == "patient":
        return user["user_id"]
    elif role == "provider":
        if not patient_id:
            raise HTTPException(status_code=400, detail="patient_id required for provider")
        _check_assignment(user["user_id"], patient_id)
        return patient_id
    elif role == "admin":
        return patient_id or user["user_id"]
    return user["user_id"]

@router.post("/", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
async def create_medicine(request: Request, medicine: MedicineCreate, user: dict = Depends(get_current_user)):
    data = medicine.model_dump(exclude_none=True)
    data["user_id"] = user["user_id"]
    data["start_date"] = data["start_date"].isoformat()
    if data.get("end_date"):
        data["end_date"] = data["end_date"].isoformat()
    if data.get("dosage_amount") is not None:
        data["dosage_amount"] = float(data["dosage_amount"])
    if "is_active" not in data:
        data["is_active"] = True
    res = supabase.table("medicines").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create medicine")
    log_audit_action("MEDICINE_CREATED", user["user_id"], {"target": res.data[0]["id"]})
    return SuccessResponse(data=res.data[0])

@router.get("/", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def list_medicines(request: Request, patient_id: str = Query(None), user: dict = Depends(get_current_user)):
    uid = _resolve_user_id(user, patient_id)
    res = supabase.table("medicines").select("*").eq("user_id", uid).eq("is_active", True).execute()
    medicines = res.data or []

    try:
        from collections import Counter
        reminders_res = supabase.table("reminders").select("*").eq("user_id", uid).eq("is_active", True).execute()
        adherence_res = supabase.table("adherence").select("reminder_id").eq("user_id", uid).eq("status", "missed").execute()

        reminders_by_med: dict[str, list] = {}
        reminder_med_map: dict[str, str] = {}
        for r in (reminders_res.data or []):
            med_id = r.get("medicine_id")
            if med_id:
                reminder_med_map[r["id"]] = med_id
                reminders_by_med.setdefault(med_id, []).append(r)

        missed_counts: Counter[str] = Counter()
        for a in (adherence_res.data or []):
            med_id = reminder_med_map.get(a.get("reminder_id"))
            if med_id:
                missed_counts[med_id] += 1

        for med in medicines:
            med["missed_count"] = missed_counts.get(med["id"], 0)
            med["reminders"] = reminders_by_med.get(med["id"], [])
            if "dosage" not in med:
                med["dosage"] = f"{med.get('dosage_amount', '')} {med.get('dosage_unit', '')}".strip()
            if "frequency" not in med:
                med["frequency"] = med.get("frequency_type", "")
    except Exception:
        for med in medicines:
            med["missed_count"] = 0
            med["reminders"] = []
            if "dosage" not in med:
                med["dosage"] = f"{med.get('dosage_amount', '')} {med.get('dosage_unit', '')}".strip()
            if "frequency" not in med:
                med["frequency"] = med.get("frequency_type", "")

    return SuccessResponse(data=medicines)

@router.get("/{id}", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def get_medicine(request: Request, id: str, user: dict = Depends(get_current_user)):
    res = supabase.table("medicines").select("*").eq("id", id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Medicine not found")
    med = res.data[0]
    role = user.get("role", "patient")
    if role == "patient" and med["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if role == "provider":
        _check_assignment(user["user_id"], med["user_id"])
    return SuccessResponse(data=med)

@router.patch("/{id}", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def update_medicine(request: Request, id: str, medicine: MedicineUpdate, user: dict = Depends(get_current_user)):
    data = medicine.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    if data.get("start_date"):
        data["start_date"] = data["start_date"].isoformat()
    if data.get("end_date"):
        data["end_date"] = data["end_date"].isoformat()
    if data.get("dosage_amount") is not None:
        data["dosage_amount"] = float(data["dosage_amount"])
    res = supabase.table("medicines").update(data).eq("id", id).eq("user_id", user["user_id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Medicine not found")
    log_audit_action("MEDICINE_UPDATED", user["user_id"], {"target": id})
    return SuccessResponse(data=res.data[0])

@router.delete("/{id}", response_model=SuccessResponse[dict])
@limiter.limit("60/minute")
async def delete_medicine(request: Request, id: str, user: dict = Depends(get_current_user)):
    supabase.table("medicines").update({"is_active": False}).eq("id", id).eq("user_id", user["user_id"]).execute()
    log_audit_action("MEDICINE_DELETED", user["user_id"], {"target": id})
    return SuccessResponse(data={"message": "Deleted."})

# --- Reminders ---

@router.get("/{id}/reminders", response_model=SuccessResponse[list])
@limiter.limit("60/minute")
async def get_reminders(request: Request, id: str, user: dict = Depends(get_current_user)):
    # First get the medicine to check ownership
    med = supabase.table("medicines").select("user_id").eq("id", id).execute()
    if not med.data:
        raise HTTPException(status_code=404, detail="Medicine not found")
    med_owner = med.data[0]["user_id"]
    role = user.get("role", "patient")
    if role == "patient" and med_owner != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if role == "provider":
        _check_assignment(user["user_id"], med_owner)
    res = supabase.table("reminders").select("*").eq("medicine_id", id).eq("is_active", True).execute()
    return SuccessResponse(data=res.data)

@router.post("/{id}/reminders", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
async def create_reminder(request: Request, id: str, reminder: dict, user: dict = Depends(get_current_user)):
    med = supabase.table("medicines").select("user_id").eq("id", id).execute()
    if not med.data:
        raise HTTPException(status_code=404, detail="Medicine not found")
    med_owner = med.data[0]["user_id"]
    role = user.get("role", "patient")
    if role == "patient" and med_owner != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if role == "provider":
        _check_assignment(user["user_id"], med_owner)

    dose_label = reminder.get("dose_label")
    if not dose_label:
        raise HTTPException(status_code=422, detail="dose_label required")
    dose_label_clean = str(dose_label).strip().lower()
    if dose_label_clean not in ("morning", "afternoon", "evening", "night"):
        raise HTTPException(status_code=422, detail="dose_label must be one of: morning, afternoon, evening, night")

    dose_time = reminder.get("dose_time_utc") or reminder.get("scheduled_time") or reminder.get("dose_time")
    if not dose_time:
        raise HTTPException(status_code=422, detail="dose_time_utc/scheduled_time required")
    if len(dose_time) == 5:
        dose_time = dose_time + ":00"

    recurrence_type = reminder.get("recurrence_type") or reminder.get("frequency_type") or "daily"
    recurrence_type_clean = str(recurrence_type).strip().lower()
    if recurrence_type_clean not in ("daily", "weekday", "alternate", "prn"):
        recurrence_type_clean = "daily"

    advance_notify = bool(
        reminder.get("advance_notify")
        or reminder.get("advance_notification")
        or (reminder.get("advance_notification_minutes", 0) > 0)
    )

    data = {
        "medicine_id": id,
        "user_id": med_owner,
        "dose_label": dose_label_clean,
        "dose_time_utc": dose_time,
        "timezone": reminder.get("timezone") or "UTC",
        "recurrence_type": recurrence_type_clean,
        "recurrence_params": reminder.get("recurrence_params"),
        "advance_notify": advance_notify
    }
    try:
        res = supabase.table("reminders").insert(data).execute()
    except Exception as e:
        if "unique_reminder_slot" in str(e) or "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail="This time slot already exists for this medicine")
        raise
    log_audit_action("REMINDER_CREATED", user["user_id"], {"target": res.data[0]["id"] if res.data else id})
    return SuccessResponse(data=res.data[0])
