from __future__ import annotations

import logging
import os
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

HOME_ASSISTANT_URL = os.getenv("HOME_ASSISTANT_URL", "http://127.0.0.1:8123").rstrip("/")
HOME_ASSISTANT_TOKEN = os.getenv("HOME_ASSISTANT_TOKEN", "")
HOME_ASSISTANT_LIGHT_ENTITY = os.getenv(
    "HOME_ASSISTANT_LIGHT_ENTITY",
    "input_boolean.cockpit_demo_switch",
)
HOME_ASSISTANT_TIMEOUT_SECONDS = float(os.getenv("HOME_ASSISTANT_TIMEOUT_SECONDS", "3"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("ha_backend")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class HomeAssistantTrigger(BaseModel):
    drivingMode: str | None = None
    driverState: str | None = None


def validate_light_entity() -> None:
    if not HOME_ASSISTANT_LIGHT_ENTITY.startswith("input_boolean."):
        raise HTTPException(
            status_code=500,
            detail="HOME_ASSISTANT_LIGHT_ENTITY must be an input_boolean entity, for example input_boolean.cockpit_demo_switch",
        )


def home_assistant_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}",
        "Content-Type": "application/json",
    }


def build_light_payload(trigger: HomeAssistantTrigger) -> dict[str, Any]:
    return {
        "entity_id": HOME_ASSISTANT_LIGHT_ENTITY,
    }


@app.post("/trigger-home-assistant")
def trigger_home_assistant(trigger: HomeAssistantTrigger) -> dict[str, Any]:
    if not HOME_ASSISTANT_TOKEN:
        logger.error("HOME_ASSISTANT_TOKEN is not configured")
        raise HTTPException(status_code=500, detail="HOME_ASSISTANT_TOKEN is not configured")

    validate_light_entity()

    driver_state = (trigger.driverState or "").strip().lower()

    if driver_state == "kritisch":
        service_name = "turn_on"
        logger.info("CRITICAL state -> activating emergency support")
    elif driver_state in {"muede", "müde"}:
        service_name = "turn_on"
        logger.info("TIRED state -> activating attention support")
    else:
        service_name = "turn_off"
        logger.info("STABLE state -> system stays passive")

    service_url = f"{HOME_ASSISTANT_URL}/api/services/input_boolean/{service_name}"
    payload = build_light_payload(trigger)

    logger.info(
        "Triggering Home Assistant input_boolean.%s entity=%s drivingMode=%s driverState=%s",
        service_name,
        payload["entity_id"],
        trigger.drivingMode,
        trigger.driverState,
    )

    try:
        response = requests.post(
            service_url,
            headers=home_assistant_headers(),
            json=payload,
            timeout=HOME_ASSISTANT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.Timeout as exc:
        logger.warning("Home Assistant request timed out after %.1fs", HOME_ASSISTANT_TIMEOUT_SECONDS)
        raise HTTPException(status_code=504, detail="Home Assistant did not respond in time") from exc
    except requests.ConnectionError as exc:
        logger.warning("Could not connect to Home Assistant at %s", HOME_ASSISTANT_URL)
        raise HTTPException(status_code=503, detail="Could not connect to Home Assistant") from exc
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 502
        response_text = exc.response.text if exc.response is not None else ""
        logger.warning("Home Assistant returned HTTP %s: %s", status_code, response_text[:500])
        raise HTTPException(
            status_code=502,
            detail=f"Home Assistant rejected input_boolean.{service_name} with HTTP {status_code}",
        ) from exc
    except requests.RequestException as exc:
        logger.exception("Unexpected Home Assistant request failure")
        raise HTTPException(status_code=502, detail="Home Assistant request failed") from exc

    logger.info("Home Assistant accepted input_boolean.%s for %s", service_name, payload["entity_id"])

    return {
        "ok": True,
        "service": f"input_boolean.{service_name}",
        "payload": payload,
    }


@app.get("/health/home-assistant")
def health_home_assistant() -> dict[str, Any]:
    if not HOME_ASSISTANT_TOKEN:
        raise HTTPException(status_code=500, detail="HOME_ASSISTANT_TOKEN is not configured")

    validate_light_entity()

    try:
        api_response = requests.get(
            f"{HOME_ASSISTANT_URL}/api/",
            headers=home_assistant_headers(),
            timeout=HOME_ASSISTANT_TIMEOUT_SECONDS,
        )
        api_response.raise_for_status()

        entity_response = requests.get(
            f"{HOME_ASSISTANT_URL}/api/states/{HOME_ASSISTANT_LIGHT_ENTITY}",
            headers=home_assistant_headers(),
            timeout=HOME_ASSISTANT_TIMEOUT_SECONDS,
        )
        entity_response.raise_for_status()
    except requests.Timeout as exc:
        logger.warning("Home Assistant health check timed out")
        raise HTTPException(status_code=504, detail="Home Assistant health check timed out") from exc
    except requests.ConnectionError as exc:
        logger.warning("Home Assistant health check could not connect to %s", HOME_ASSISTANT_URL)
        raise HTTPException(status_code=503, detail="Could not connect to Home Assistant") from exc
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 502
        logger.warning("Home Assistant health check failed with HTTP %s", status_code)
        raise HTTPException(
            status_code=502,
            detail=f"Home Assistant health check failed with HTTP {status_code}",
        ) from exc
    except requests.RequestException as exc:
        logger.exception("Unexpected Home Assistant health check failure")
        raise HTTPException(status_code=502, detail="Home Assistant health check failed") from exc

    return {
        "ok": True,
        "homeAssistantUrl": HOME_ASSISTANT_URL,
        "entity": HOME_ASSISTANT_LIGHT_ENTITY,
    }
