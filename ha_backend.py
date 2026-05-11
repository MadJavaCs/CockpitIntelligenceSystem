from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover - keeps the demo API stable if paho-mqtt is not installed yet.
    mqtt = None

HOME_ASSISTANT_URL = os.getenv("HOME_ASSISTANT_URL", "http://127.0.0.1:8123").rstrip("/")
HOME_ASSISTANT_TOKEN = os.getenv("HOME_ASSISTANT_TOKEN", "")
HOME_ASSISTANT_LIGHT_ENTITY = os.getenv(
    "HOME_ASSISTANT_LIGHT_ENTITY",
    "input_boolean.cockpit_demo_switch",
)
HOME_ASSISTANT_TIMEOUT_SECONDS = float(os.getenv("HOME_ASSISTANT_TIMEOUT_SECONDS", "3"))
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "porsche/driver/state")
MQTT_TIMEOUT_SECONDS = float(os.getenv("MQTT_TIMEOUT_SECONDS", "2"))

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("ha_backend")
MQTT_CLIENT: Any | None = None
LAST_MQTT_EVENT: dict[str, Any] | None = None
LAST_HOME_ASSISTANT_STATUS: dict[str, Any] | None = None
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
    riskIndex: int | None = None
    supportStrategy: str | None = None
    triggerReason: str | None = None


def validate_light_entity(raise_on_error: bool = True) -> bool:
    is_valid = HOME_ASSISTANT_LIGHT_ENTITY.startswith("input_boolean.")
    if not is_valid and raise_on_error:
        raise HTTPException(
            status_code=500,
            detail="HOME_ASSISTANT_LIGHT_ENTITY must be an input_boolean entity, for example input_boolean.cockpit_demo_switch",
        )
    return is_valid


def home_assistant_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}",
        "Content-Type": "application/json",
    }


def build_light_payload(trigger: HomeAssistantTrigger) -> dict[str, Any]:
    return {
        "entity_id": HOME_ASSISTANT_LIGHT_ENTITY,
    }


def build_mqtt_payload(trigger: HomeAssistantTrigger) -> dict[str, Any]:
    payload = {
        "driverState": trigger.driverState,
        "drivingMode": trigger.drivingMode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if trigger.riskIndex is not None:
        payload["riskIndex"] = trigger.riskIndex
    if trigger.supportStrategy:
        payload["supportStrategy"] = trigger.supportStrategy
    if trigger.triggerReason:
        payload["triggerReason"] = trigger.triggerReason
    return payload


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def remember_home_assistant_status(status: dict[str, Any]) -> dict[str, Any]:
    global LAST_HOME_ASSISTANT_STATUS
    LAST_HOME_ASSISTANT_STATUS = status
    return status


def build_home_assistant_status(
    *,
    ok: bool,
    status: str,
    service: str | None,
    payload: dict[str, Any],
    last_error: str | None = None,
    http_status: int | None = None,
) -> dict[str, Any]:
    return remember_home_assistant_status({
        "ok": ok,
        "status": status,
        "service": service,
        "entity": HOME_ASSISTANT_LIGHT_ENTITY,
        "payload": payload,
        "httpStatus": http_status,
        "lastError": last_error,
        "timestamp": utc_timestamp(),
    })


def create_mqtt_client() -> Any:
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except (AttributeError, TypeError):
        return mqtt.Client()


@app.on_event("startup")
def startup_mqtt_client() -> None:
    global MQTT_CLIENT

    if mqtt is None:
        logger.warning("paho-mqtt is not installed; MQTT publishing is disabled")
        return

    MQTT_CLIENT = create_mqtt_client()

    try:
        MQTT_CLIENT.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        MQTT_CLIENT.loop_start()
        logger.info("MQTT client connected to %s:%s", MQTT_HOST, MQTT_PORT)
    except Exception as exc:
        MQTT_CLIENT = None
        logger.warning("MQTT startup connection failed for %s:%s: %s", MQTT_HOST, MQTT_PORT, exc)


@app.on_event("shutdown")
def shutdown_mqtt_client() -> None:
    if MQTT_CLIENT is None:
        return

    try:
        MQTT_CLIENT.loop_stop()
        MQTT_CLIENT.disconnect()
    except Exception as exc:
        logger.warning("MQTT shutdown failed: %s", exc)


def remember_mqtt_event(result: dict[str, Any]) -> dict[str, Any]:
    global LAST_MQTT_EVENT
    LAST_MQTT_EVENT = result
    return result


def publish_mqtt_event(trigger: HomeAssistantTrigger) -> dict[str, Any]:
    payload = build_mqtt_payload(trigger)

    if mqtt is None:
        logger.warning("paho-mqtt is not installed; MQTT event prepared but not sent")
        return remember_mqtt_event({
            "sent": False,
            "status": "prepared_not_sent",
            "topic": MQTT_TOPIC,
            "payload": payload,
            "lastError": "paho-mqtt is not installed",
            "timestamp": utc_timestamp(),
        })

    if MQTT_CLIENT is None:
        logger.warning("MQTT client is not connected; event prepared but not sent")
        return remember_mqtt_event({
            "sent": False,
            "status": "prepared_not_sent",
            "topic": MQTT_TOPIC,
            "payload": payload,
            "lastError": "MQTT client is not connected",
            "timestamp": utc_timestamp(),
        })

    try:
        info = MQTT_CLIENT.publish(MQTT_TOPIC, json.dumps(payload), qos=0, retain=False)
        info.wait_for_publish(timeout=MQTT_TIMEOUT_SECONDS)
        if not info.is_published():
            raise TimeoutError("MQTT publish timed out")
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(mqtt.error_string(info.rc))
    except Exception as exc:
        logger.warning("MQTT publish failed for topic=%s: %s", MQTT_TOPIC, exc)
        return remember_mqtt_event({
            "sent": False,
            "status": "prepared_not_sent",
            "topic": MQTT_TOPIC,
            "payload": payload,
            "lastError": str(exc),
            "timestamp": utc_timestamp(),
        })

    logger.info("Published MQTT event topic=%s payload=%s", MQTT_TOPIC, payload)
    return remember_mqtt_event({
        "sent": True,
        "status": "published",
        "topic": MQTT_TOPIC,
        "payload": payload,
        "lastError": None,
        "timestamp": utc_timestamp(),
    })


@app.post("/trigger-home-assistant")
def trigger_home_assistant(trigger: HomeAssistantTrigger) -> dict[str, Any]:
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
    mqtt_result = publish_mqtt_event(trigger)

    if not HOME_ASSISTANT_TOKEN:
        last_error = "HOME_ASSISTANT_TOKEN is not configured"
        logger.warning("Home Assistant trigger skipped: %s", last_error)
        ha_status = build_home_assistant_status(
            ok=False,
            status="not_configured",
            service=f"input_boolean.{service_name}",
            payload=payload,
            last_error=last_error,
        )
        return build_trigger_response(ha_status, mqtt_result)

    if not validate_light_entity(raise_on_error=False):
        last_error = (
            "HOME_ASSISTANT_LIGHT_ENTITY must be an input_boolean entity, "
            "for example input_boolean.cockpit_demo_switch"
        )
        logger.warning("Home Assistant trigger skipped: %s", last_error)
        ha_status = build_home_assistant_status(
            ok=False,
            status="invalid_entity",
            service=f"input_boolean.{service_name}",
            payload=payload,
            last_error=last_error,
        )
        return build_trigger_response(ha_status, mqtt_result)

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
        last_error = f"Home Assistant did not respond within {HOME_ASSISTANT_TIMEOUT_SECONDS:.1f}s"
        logger.warning("%s url=%s", last_error, service_url)
        ha_status = build_home_assistant_status(
            ok=False,
            status="timeout",
            service=f"input_boolean.{service_name}",
            payload=payload,
            last_error=last_error,
        )
        return build_trigger_response(ha_status, mqtt_result)
    except requests.ConnectionError as exc:
        last_error = f"Could not connect to Home Assistant at {HOME_ASSISTANT_URL}"
        logger.warning("%s: %s", last_error, exc)
        ha_status = build_home_assistant_status(
            ok=False,
            status="unreachable",
            service=f"input_boolean.{service_name}",
            payload=payload,
            last_error=last_error,
        )
        return build_trigger_response(ha_status, mqtt_result)
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 502
        response_text = exc.response.text if exc.response is not None else ""
        logger.warning("Home Assistant returned HTTP %s: %s", status_code, response_text[:500])
        ha_status = build_home_assistant_status(
            ok=False,
            status="rejected",
            service=f"input_boolean.{service_name}",
            payload=payload,
            last_error=f"Home Assistant rejected input_boolean.{service_name} with HTTP {status_code}",
            http_status=status_code,
        )
        return build_trigger_response(ha_status, mqtt_result)
    except requests.RequestException as exc:
        last_error = f"Home Assistant request failed: {exc}"
        logger.exception("Unexpected Home Assistant request failure")
        ha_status = build_home_assistant_status(
            ok=False,
            status="request_failed",
            service=f"input_boolean.{service_name}",
            payload=payload,
            last_error=last_error,
        )
        return build_trigger_response(ha_status, mqtt_result)

    logger.info("Home Assistant accepted input_boolean.%s for %s", service_name, payload["entity_id"])
    ha_status = build_home_assistant_status(
        ok=True,
        status="sent",
        service=f"input_boolean.{service_name}",
        payload=payload,
        http_status=response.status_code,
    )

    return build_trigger_response(ha_status, mqtt_result)


def build_trigger_response(ha_status: dict[str, Any], mqtt_result: dict[str, Any]) -> dict[str, Any]:
    last_error = ha_status.get("lastError") or mqtt_result.get("lastError")
    return {
        "ok": bool(ha_status.get("ok")),
        "homeAssistantStatus": ha_status,
        "mqttStatus": {
            "ok": bool(mqtt_result.get("sent")),
            "sent": bool(mqtt_result.get("sent")),
            "status": mqtt_result.get("status", "unknown"),
            "topic": mqtt_result.get("topic"),
            "lastError": mqtt_result.get("lastError"),
            "timestamp": mqtt_result.get("timestamp"),
        },
        "lastError": last_error,
        "lastEvent": mqtt_result.get("payload"),
        "service": ha_status.get("service"),
        "payload": ha_status.get("payload"),
        "mqtt": mqtt_result,
    }


@app.get("/mqtt/last-event")
def mqtt_last_event() -> dict[str, Any]:
    return {
        "ok": LAST_MQTT_EVENT is not None,
        "homeAssistantStatus": LAST_HOME_ASSISTANT_STATUS,
        "mqtt": LAST_MQTT_EVENT,
        "lastError": (LAST_HOME_ASSISTANT_STATUS or {}).get("lastError")
        or (LAST_MQTT_EVENT or {}).get("lastError"),
        "lastEvent": (LAST_MQTT_EVENT or {}).get("payload"),
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
