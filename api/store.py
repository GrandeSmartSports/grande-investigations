import json
import os
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def _file(collection: str) -> Path:
    return DATA_DIR / f"{collection}.json"


def load(collection: str) -> list[dict]:
    f = _file(collection)
    if not f.exists():
        return []
    return json.loads(f.read_text())


def save(collection: str, data: list[dict]):
    _file(collection).write_text(json.dumps(data, indent=2))


def find(collection: str, id: str) -> Optional[dict]:
    for item in load(collection):
        if item.get("id") == id:
            return item
    return None


def upsert(collection: str, item: dict):
    data = load(collection)
    for i, existing in enumerate(data):
        if existing.get("id") == item["id"]:
            data[i] = item
            save(collection, data)
            return
    data.append(item)
    save(collection, data)


def delete(collection: str, id: str) -> bool:
    data = load(collection)
    new_data = [d for d in data if d.get("id") != id]
    if len(new_data) == len(data):
        return False
    save(collection, new_data)
    return True
