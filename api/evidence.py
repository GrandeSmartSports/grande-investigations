from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
from . import store
from .auth import verify_pin

router = APIRouter(prefix="/api/cases/{case_id}/evidence", dependencies=[Depends(verify_pin)])

COLLECTION = "evidence"


class GpsPoint(BaseModel):
    lat: float = 0
    lng: float = 0


class EvidenceCreate(BaseModel):
    type: str = "photo"
    filename: str = ""
    description: str = ""
    captured_by: str = "daniel"
    captured_at: Optional[str] = None
    gps: Optional[GpsPoint] = None


@router.post("")
def create_evidence(case_id: str, body: EvidenceCreate):
    # Verify case exists
    case = store.find("cases", case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    now = datetime.utcnow().isoformat()
    captured_at = body.captured_at or now
    gps_data = body.gps.dict() if body.gps else {"lat": 0, "lng": 0}

    evidence = {
        "id": f"ev-{uuid.uuid4().hex[:8]}",
        "case_id": case_id,
        "type": body.type,
        "filename": body.filename,
        "description": body.description,
        "captured_by": body.captured_by,
        "captured_at": captured_at,
        "gps": gps_data,
        "chain_of_custody": [
            {"action": "captured", "by": body.captured_by, "at": captured_at, "gps": gps_data}
        ],
        "created_at": now,
    }
    store.upsert(COLLECTION, evidence)
    return evidence


@router.get("")
def list_evidence(case_id: str):
    all_ev = store.load(COLLECTION)
    return [e for e in all_ev if e.get("case_id") == case_id]


@router.delete("/{evidence_id}")
def delete_evidence(case_id: str, evidence_id: str):
    ev = store.find(COLLECTION, evidence_id)
    if not ev or ev.get("case_id") != case_id:
        raise HTTPException(404, "Evidence not found")
    store.delete(COLLECTION, evidence_id)
    return {"ok": True}
