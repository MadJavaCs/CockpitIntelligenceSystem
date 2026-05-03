from __future__ import annotations

import os
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


HOME_ASSISTANT_URL = os.getenv("HOME_ASSISTANT_URL", "http://127.0.0.1:8123").rstrip("/")
HOME_ASSISTANT_TOKEN = os.getenv("HOME_ASSISTANT_TOKEN", "")
HOME_ASSISTANT_LIGHT_ENTITY = os.getenv("HOME_ASSISTANT_LIGHT_ENTITY", "light.porsche_cockpit")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class HomeAssistantTrigger(BaseModel):
    drivingMode: str | None = None
    driverState: str | None = None


def build_light_payload(trigger: HomeAssistantTrigger) -> dict[str, Any]:
    driving_mode = (trigger.drivingMode or "").strip().lower()
    driver_state = (trigger.driverState or "").strip().lower()

    if driving_mode == "warnmodus" or driver_state == "kritisch":
        return {
            "entity_id": HOME_ASSISTANT_LIGHT_ENTITY,
            "rgb_color": [255, 0, 0],
            "brightness": 255,
        }

    if driver_state in {"muede", "müde"}:
        return {
            "entity_id": HOME_ASSISTANT_LIGHT_ENTITY,
            "color_temp_kelvin": 2700,
            "brightness": 90,
        }

    return {
        "entity_id": HOME_ASSISTANT_LIGHT_ENTITY,
        "rgb_color": [255, 184, 77],
        "brightness": 140,
    }


@app.post("/trigger-home-assistant")
def trigger_home_assistant(trigger: HomeAssistantTrigger) -> dict[str, Any]:
    if not HOME_ASSISTANT_TOKEN:
        raise HTTPException(status_code=500, detail="HOME_ASSISTANT_TOKEN is not configured")

    service_url = f"{HOME_ASSISTANT_URL}/api/services/light/turn_on"
    payload = build_light_payload(trigger)
    response = requests.post(
        service_url,
        headers={
            "Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=5,
    )

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return {
        "ok": True,
        "service": "light.turn_on",
        "payload": payload,
    }
