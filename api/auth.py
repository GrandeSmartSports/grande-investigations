from fastapi import Header, HTTPException
import os

# Simple PIN auth - upgrade to JWT later
APP_PIN = os.environ.get("APP_PIN", "1234")


def verify_pin(x_pin: str = Header(default=None)):
    if not x_pin or x_pin != APP_PIN:
        raise HTTPException(status_code=401, detail="Invalid PIN")
