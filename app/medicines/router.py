from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.db.supabase import supabase_admin
from app.auth.dependencies import get_current_user
from app.core.responses import SuccessResponse
from app.medicines.schemas import MedicineCreate, MedicineUpdate, ReminderCreate, ReminderUpdate
from app.services.audit import log_audit_action

router = APIRouter()

def _check_assignment(provider_id: str, patient_id: str):
    """Verify provider is assigned to patient. Raises 403 if not."""
    res = supabase_admin.table("assignments").select("id").eq("provider_id", provider_id).eq("patient_id", patient_id).eq("status", "active").execute()
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
async def create_medicine(medicine: MedicineCreate, user: dict = Depends(get_current_user)):
    data = medicine.model_dump()
    data["user_id"] = user["user_id"]
    data["start_date"] = data["start_date"].isoformat()
    if data["end_date"]: data["end_date"] = data["end_date"].isoformat()
    res = supabase_admin.table("medicines").insert(data).execute()
    return SuccessResponse(data=res.data[0])

@router.get("/", response_model=SuccessResponse[list])
async def list_medicines(patient_id: str = Query(None), user: dict = Depends(get_current_user)):
    uid = _resolve_user_id(user, patient_id)
    res = supabase_admin.table("medicines").select("*").eq("user_id", uid).eq("is_active", True).execute()
    return SuccessResponse(data=res.data)

@router.get("/{id}", response_model=SuccessResponse[dict])
async def get_medicine(id: str, user: dict = Depends(get_current_user)):
    res = supabase_admin.table("medicines").select("*").eq("id", id).execute()
    if not res.data: raise HTTPException(status_code=404, detail="Medicine not found")
    med = res.data[0]
    role = user.get("role", "patient")
    if role == "patient" and med["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if role == "provider":
        _check_assignment(user["user_id"], med["user_id"])
    return SuccessResponse(data=med)

@router.patch("/{id}", response_model=SuccessResponse[dict])
async def update_medicine(id: str, medicine: MedicineUpdate, user: dict = Depends(get_current_user)):
    data = medicine.model_dump(exclude_unset=True)
    res = supabase_admin.table("medicines").update(data).eq("id", id).eq("user_id", user["user_id"]).execute()
    if not res.data: raise HTTPException(status_code=404, detail="Medicine not found")
    return SuccessResponse(data=res.data[0])

@router.delete("/{id}", response_model=SuccessResponse[dict])
async def delete_medicine(id: str, user: dict = Depends(get_current_user)):
    supabase_admin.table("medicines").update({"is_active": False}).eq("id", id).eq("user_id", user["user_id"]).execute()
    return SuccessResponse(data={"message": "Deleted."})

# --- Reminders ---

@router.get("/{id}/reminders", response_model=SuccessResponse[list])
async def get_reminders(id: str, user: dict = Depends(get_current_user)):
    # First get the medicine to check ownership
    med = supabase_admin.table("medicines").select("user_id").eq("id", id).execute()
    if not med.data: raise HTTPException(status_code=404, detail="Medicine not found")
    med_owner = med.data[0]["user_id"]
    role = user.get("role", "patient")
    if role == "patient" and med_owner != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if role == "provider":
        _check_assignment(user["user_id"], med_owner)
    res = supabase_admin.table("reminders").select("*").eq("medicine_id", id).eq("is_active", True).execute()
    return SuccessResponse(data=res.data)

@router.post("/{id}/reminders", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_reminder(id: str, reminder: ReminderCreate, user: dict = Depends(get_current_user)):
    med = supabase_admin.table("medicines").select("user_id").eq("id", id).execute()
    if not med.data: raise HTTPException(status_code=404, detail="Medicine not found")
    med_owner = med.data[0]["user_id"]
    role = user.get("role", "patient")
    if role == "patient" and med_owner != user["user_id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    if role == "provider":
        _check_assignment(user["user_id"], med_owner)
    data = reminder.model_dump()
    data["medicine_id"] = id
    data["user_id"] = med_owner
    try:
        res = supabase_admin.table("reminders").insert(data).execute()
    except Exception as e:
        if "unique_reminder_slot" in str(e) or "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail="This time slot already exists for this medicine")
        raise
    log_audit_action("REMINDER_CREATED", user["user_id"], {"target": res.data[0]["id"] if res.data else id})
    return SuccessResponse(data=res.data[0])
