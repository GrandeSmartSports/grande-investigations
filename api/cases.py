from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
from . import store
from .auth import verify_pin

router = APIRouter(prefix="/api/cases", dependencies=[Depends(verify_pin)])

COLLECTION = "cases"


class ClientInfo(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""


class SubjectInfo(BaseModel):
    name: str = ""
    aliases: list[str] = []
    dob: str = ""
    last_known_address: str = ""


class BillingInfo(BaseModel):
    rate_type: str = "hourly"
    rate: float = 0
    hours: float = 0
    expenses: list[dict] = []


class CaseCreate(BaseModel):
    type: str = "background_check"
    title: str
    client: ClientInfo = ClientInfo()
    subject: SubjectInfo = SubjectInfo()
    priority: str = "medium"
    assigned_to: str = "daniel"
    billing: BillingInfo = BillingInfo()


class CaseUpdate(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    client: Optional[ClientInfo] = None
    subject: Optional[SubjectInfo] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    billing: Optional[BillingInfo] = None


class NoteAdd(BaseModel):
    text: str
    author: str = "daniel"


@router.post("")
def create_case(body: CaseCreate):
    now = datetime.utcnow().isoformat()
    case = {
        "id": f"case-{uuid.uuid4().hex[:8]}",
        "type": body.type,
        "title": body.title,
        "client": body.client.model_dump(),
        "subject": body.subject.model_dump(),
        "status": "intake",
        "priority": body.priority,
        "assigned_to": body.assigned_to,
        "notes": [],
        "evidence": [],
        "timeline": [{"event": "Case created", "at": now}],
        "billing": body.billing.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    store.upsert(COLLECTION, case)
    return case


@router.get("")
def list_cases(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
):
    cases = store.load(COLLECTION)
    if type:
        cases = [c for c in cases if c.get("type") == type]
    if status:
        cases = [c for c in cases if c.get("status") == status]
    if assigned_to:
        cases = [c for c in cases if c.get("assigned_to") == assigned_to]
    return cases


@router.get("/{case_id}")
def get_case(case_id: str):
    case = store.find(COLLECTION, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    return case


@router.patch("/{case_id}")
def update_case(case_id: str, body: CaseUpdate):
    case = store.find(COLLECTION, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    updates = body.model_dump(exclude_none=True)
    for key, val in updates.items():
        if isinstance(val, dict):
            case[key] = val
        else:
            case[key] = val
    case["updated_at"] = datetime.utcnow().isoformat()
    case["timeline"].append({"event": f"Case updated: {list(updates.keys())}", "at": case["updated_at"]})
    store.upsert(COLLECTION, case)
    return case


@router.delete("/{case_id}")
def archive_case(case_id: str):
    case = store.find(COLLECTION, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    case["status"] = "closed"
    case["updated_at"] = datetime.utcnow().isoformat()
    case["timeline"].append({"event": "Case archived", "at": case["updated_at"]})
    store.upsert(COLLECTION, case)
    return {"ok": True}


@router.post("/{case_id}/notes")
def add_note(case_id: str, body: NoteAdd):
    case = store.find(COLLECTION, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    note = {
        "id": uuid.uuid4().hex[:8],
        "text": body.text,
        "author": body.author,
        "at": datetime.utcnow().isoformat(),
    }
    case["notes"].append(note)
    case["updated_at"] = note["at"]
    case["timeline"].append({"event": f"Note added by {body.author}", "at": note["at"]})
    store.upsert(COLLECTION, case)
    return note
