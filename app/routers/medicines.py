import logging
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import MedicineCreate, MedicineUpdate, Medicine
from app.db.supabase import supabase
from app.auth.dependencies import get_current_user

logger = logging.getLogger("adhera.medicines")
router = APIRouter()


def _serialize_medicine_data(data: dict) -> dict:
    """Convert date objects to ISO strings for Supabase."""
    for field in ("start_date", "end_date"):
        if field in data and data[field] is not None:
            if isinstance(data[field], date):
                data[field] = data[field].isoformat()
    return data


@router.post("/", response_model=Medicine, status_code=status.HTTP_201_CREATED)
async def create_medicine(medicine: MedicineCreate, user: dict = Depends(get_current_user)):
    """Add a new medicine to the authenticated user's regimen."""
    today = datetime.now(timezone.utc).date()
    if medicine.start_date < today:
        raise HTTPException(status_code=400, detail="start_date cannot be in the past.")

    data = _serialize_medicine_data(medicine.model_dump())
    data["user_id"] = user["user_id"]
    data["is_active"] = True

    response = supabase.table("medicines").insert(data).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Could not create medicine.")

    return response.data[0]


@router.get("/", response_model=list[Medicine])
async def list_medicines(user: dict = Depends(get_current_user)):
    """List all active medicines for the authenticated user."""
    response = (
        supabase.table("medicines")
        .select("*")
        .eq("user_id", user["user_id"])
        .eq("is_active", True)
        .execute()
    )
    return response.data


@router.get("/{medicine_id}", response_model=Medicine)
async def get_medicine(medicine_id: str, user: dict = Depends(get_current_user)):
    """Fetch a single medicine by ID."""
    response = (
        supabase.table("medicines")
        .select("*")
        .eq("id", medicine_id)
        .eq("user_id", user["user_id"])
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Medicine not found.")
    return response.data[0]


@router.patch("/{medicine_id}", response_model=Medicine)
async def update_medicine(
    medicine_id: str, medicine: MedicineUpdate, user: dict = Depends(get_current_user)
):
    """Partially update a medicine."""
    data = medicine.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    data = _serialize_medicine_data(data)

    response = (
        supabase.table("medicines")
        .update(data)
        .eq("id", medicine_id)
        .eq("user_id", user["user_id"])
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Medicine not found.")
    return response.data[0]


@router.delete("/{medicine_id}", status_code=status.HTTP_200_OK)
async def delete_medicine(medicine_id: str, user: dict = Depends(get_current_user)):
    """Soft-delete a medicine (sets is_active=False)."""
    response = (
        supabase.table("medicines")
        .update({"is_active": False})
        .eq("id", medicine_id)
        .eq("user_id", user["user_id"])
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Medicine not found.")
    return {"message": "Medicine deleted."}
