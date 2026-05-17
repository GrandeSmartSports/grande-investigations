from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
from . import store
from .auth import verify_pin

router = APIRouter(prefix="/api/serves", dependencies=[Depends(verify_pin)])

COLLECTION = "serves"


class GpsPoint(BaseModel):
    lat: float = 0
    lng: float = 0


class SubjectInfo(BaseModel):
    name: str = ""
    address: str = ""
    description: str = ""


class MileageInfo(BaseModel):
    start: float = 0
    end: float = 0
    total: float = 0


class ServeCreate(BaseModel):
    case_id: str
    subject: Optional[SubjectInfo] = None
    documents: str = ""
    assigned_to: str = "daniel"


class ServeUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    documents: Optional[str] = None
    mileage: Optional[MileageInfo] = None
    served_at: Optional[str] = None
    served_gps: Optional[GpsPoint] = None


class AttemptCreate(BaseModel):
    gps: Optional[GpsPoint] = None
    result: str = "not_home"
    notes: str = ""
    photo_evidence_id: str = ""


@router.post("")
def create_serve(body: ServeCreate):
    case = store.find("cases", body.case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    now = datetime.utcnow().isoformat()
    subject_data = body.subject.dict() if body.subject else {"name": "", "address": "", "description": ""}

    serve = {
        "id": f"srv-{uuid.uuid4().hex[:8]}",
        "case_id": body.case_id,
        "subject": subject_data,
        "documents": body.documents,
        "status": "assigned",
        "assigned_to": body.assigned_to,
        "attempts": [],
        "served_at": None,
        "served_gps": None,
        "mileage": {"start": 0, "end": 0, "total": 0},
        "created_at": now,
        "updated_at": now,
    }
    store.upsert(COLLECTION, serve)
    return serve


@router.get("")
def list_serves(
    status: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    case_id: Optional[str] = Query(None),
):
    serves = store.load(COLLECTION)
    if status:
        serves = [s for s in serves if s.get("status") == status]
    if assigned_to:
        serves = [s for s in serves if s.get("assigned_to") == assigned_to]
    if case_id:
        serves = [s for s in serves if s.get("case_id") == case_id]
    return serves


@router.get("/{serve_id}")
def get_serve(serve_id: str):
    serve = store.find(COLLECTION, serve_id)
    if not serve:
        raise HTTPException(404, "Serve not found")
    return serve


@router.patch("/{serve_id}")
def update_serve(serve_id: str, body: ServeUpdate):
    serve = store.find(COLLECTION, serve_id)
    if not serve:
        raise HTTPException(404, "Serve not found")

    updates = body.dict(exclude_none=True)
    for key, val in updates.items():
        if isinstance(val, dict):
            serve[key] = val
        else:
            serve[key] = val
    serve["updated_at"] = datetime.utcnow().isoformat()
    store.upsert(COLLECTION, serve)
    return serve


@router.post("/{serve_id}/attempts")
def log_attempt(serve_id: str, body: AttemptCreate):
    serve = store.find(COLLECTION, serve_id)
    if not serve:
        raise HTTPException(404, "Serve not found")

    now = datetime.utcnow().isoformat()
    gps_data = body.gps.dict() if body.gps else {"lat": 0, "lng": 0}

    attempt = {
        "id": f"att-{uuid.uuid4().hex[:8]}",
        "at": now,
        "gps": gps_data,
        "result": body.result,
        "notes": body.notes,
        "photo_evidence_id": body.photo_evidence_id,
    }
    serve["attempts"].append(attempt)
    serve["updated_at"] = now

    if body.result == "served":
        serve["status"] = "served"
        serve["served_at"] = now
        serve["served_gps"] = gps_data
    elif serve["status"] == "assigned":
        serve["status"] = "in_progress"

    store.upsert(COLLECTION, serve)
    return attempt
