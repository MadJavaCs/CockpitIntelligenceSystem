from __future__ import annotations

import json
import mimetypes
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from home_assistant import HomeAssistantClient
from logic import analyze_driver_state
from state import Systemzustand


HOST = "127.0.0.1"
PORT = 8000
BASE_DIR = Path(__file__).resolve().parent
STATIC_FILES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/style.css": "style.css",
    "/script.js": "script.js",
}


@dataclass
class PorscheAssistantBackend:
    systemzustand: Systemzustand = field(
        default_factory=lambda: Systemzustand(kontext="Initialisierung", ist_aktiv=False)
    )
    override_mode: bool = False
    previous_driver_state: str | None = None
    previous_risk_score: int | None = None
    home_assistant: HomeAssistantClient = field(default_factory=HomeAssistantClient)

    def build_dashboard_state(self) -> dict[str, Any]:
        now = datetime.now()
        home_assistant_data = self._get_home_assistant_data()
        uhrzeit = home_assistant_data.get("uhrzeit", now.strftime("%H:%M"))
        outside_temperature = self._get_outside_temperature(home_assistant_data)
        context_hour = self._get_context_hour(uhrzeit, now.hour)
        time_context = self._get_time_context(context_hour, home_assistant_data)
        driving_context = self._get_driving_context(context_hour, home_assistant_data)
        weather = self._get_weather_context(context_hour, home_assistant_data)
        critical_maneuver = self._get_critical_maneuver(home_assistant_data)
        context = {
            "uhrzeit": uhrzeit,
            "driving_context": driving_context,
            "weather": weather,
            "outside_temperature": outside_temperature,
            "critical_maneuver": critical_maneuver,
            **home_assistant_data,
        }
        result = self._analyze_context(context)

        self.systemzustand = Systemzustand(
            kontext="Night Operation" if time_context["is_night"] else "Day Operation",
            ist_aktiv=True,
        )

        assessment = result["assessment"]
        telemetry = result["telemetry"]
        warning_level = str(assessment["warnstufe"])
        risk_score = int(assessment["risiko_score"])
        driver_state = self._format_driver_state(str(assessment["fahrerzustand"]))
        self.previous_driver_state = str(assessment["fahrerzustand"])
        self.previous_risk_score = risk_score
        system_mode = self._derive_system_mode(driver_state)
        driving_mode = self._derive_driving_mode(risk_score)

        return {
            "system": {
                "online": self.systemzustand.ist_aktiv,
                "overrideMode": self.override_mode,
                "systemLabel": "System Online" if self.systemzustand.ist_aktiv else "System Offline",
            },
            "time": {
                "clock": uhrzeit,
                "date": now.strftime("%d %B %Y"),
                "phase": self.systemzustand.kontext,
            },
            "context": {
                "drivingContext": driving_context,
                "weather": weather,
                "timeOfDay": time_context["time_of_day"],
                "isNight": time_context["is_night"],
                "timeSource": time_context["source"],
                "criticalManeuver": critical_maneuver,
                "route": self._derive_route(driving_context),
                "traffic": self._derive_traffic(driving_context),
                "homeAssistant": home_assistant_data.get("kalenderstatus", "Keine Home-Assistant-Daten"),
                "weatherSensor": self._build_weather_sensor(home_assistant_data, outside_temperature),
            },
            "telemetry": {
                "stress": int(telemetry["stresslevel"]),
                "energy": int(telemetry["energielevel"]),
                "focus": int(telemetry["fokuslevel"]),
                "cameraStatus": self._derive_camera_status(int(telemetry["fokuslevel"])),
                "wheelContact": self._derive_wheel_contact(int(telemetry["stresslevel"])),
                "cabinState": self._derive_cabin_state(int(telemetry["stresslevel"])),
                "inputSummary": self._build_input_summary(driving_context, weather, risk_score),
            },
            "assessment": {
                "driverState": driver_state,
                "systemMode": system_mode["label"],
                "systemModeKey": system_mode["key"],
                "mode": driving_mode,
                "riskScore": risk_score,
                "riskFormula": str(assessment.get("risiko_formel", "")),
                "distractionState": str(assessment.get("distraction_state", "keine Ablenkung")),
                "distractionModifier": int(assessment.get("distraction_modifier", 0)),
                "nightModifier": int(assessment.get("night_modifier", 0)),
                "weatherImpact": int(assessment.get("weather_modifier", 0)),
                "criticalManeuverImpact": int(assessment.get("critical_maneuver_modifier", 0)),
                "sensorModifier": int(assessment.get("heart_rate_modifier", 0)),
                "awarenessBoostImpact": int(assessment.get("awareness_coupling_modifier", 0)),
                "riskRandomOffset": int(assessment.get("risiko_random_offset", 0)),
                "riskTrend": str(assessment.get("risiko_trend", "stable")),
                "warningLevel": warning_level,
                "recommendation": str(assessment["empfehlung"]),
                "criticalManeuverState": critical_maneuver,
                "criticalManeuverStrategy": self._derive_critical_maneuver_strategy(critical_maneuver),
                "reason": str(assessment["begruendung"]),
                "assistReaction": str(assessment.get("assist_reaction") or self._derive_assist_reaction(
                    warning_level,
                    int(telemetry["fokuslevel"]),
                    str(assessment.get("distraction_state", "keine Ablenkung")),
                )),
                "lightMode": str(assessment["lichtmodus"]),
                "supportStrategy": str(assessment.get("support_strategy", "")),
                "triggerReason": str(assessment.get("trigger_reason", "")),
                "aiTitle": "Adaptive Support Strategy",
                "aiSummary": self._build_ai_summary(
                    str(assessment["modus"]),
                    str(assessment["empfehlung"]),
                    critical_maneuver,
                ),
                "coffeeRecommendation": self._capitalize(str(assessment["coffee_recommendation"])),
                "coffeeReason": str(assessment["coffee_reason"]),
                "warningTitle": self._derive_warning_title(warning_level),
                "warningPriority": self._derive_warning_priority(warning_level),
                "warningTrigger": str(assessment.get("trigger_reason") or self._derive_warning_trigger(
                    driving_context,
                    weather,
                    int(telemetry["energielevel"]),
                    int(telemetry["stresslevel"]),
                )),
                "warningAction": self._derive_warning_action(
                    warning_level,
                    str(assessment["empfehlung"]),
                    critical_maneuver,
                ),
            },
        }

    def _analyze_context(self, context: dict[str, str]) -> dict[str, dict[str, str | int]]:
        return analyze_driver_state(
            context["uhrzeit"],
            context["driving_context"],
            context.get("weather", "Klar"),
            self._coerce_temperature(context.get("outside_temperature")),
            context.get("critical_maneuver", "none"),
            self._coerce_heart_rate(context.get("heart_rate") or context.get("heartRate")),
            self.previous_driver_state,
            self.previous_risk_score,
        )

    def _get_home_assistant_data(self) -> dict[str, str]:
        try:
            return self.home_assistant.get_context_data()
        except Exception:
            return {}

    def _coerce_temperature(self, value: Any) -> int | None:
        if value in {None, ""}:
            return None
        try:
            return int(float(str(value).replace(",", ".")))
        except (TypeError, ValueError):
            return None

    def _coerce_heart_rate(self, value: Any) -> int | None:
        if value in {None, ""}:
            return None
        try:
            return int(float(str(value).replace(",", ".")))
        except (TypeError, ValueError):
            return None

    def _get_outside_temperature(self, home_assistant_data: dict[str, str]) -> int | None:
        return self._coerce_temperature(
            home_assistant_data.get("outside_temperature")
            or home_assistant_data.get("outsideTemperature")
            or home_assistant_data.get("aussentemperatur")
        )

    def _get_context_hour(self, uhrzeit: str, fallback_hour: int) -> int:
        try:
            return int(uhrzeit.split(":", maxsplit=1)[0])
        except (TypeError, ValueError, AttributeError):
            return fallback_hour

    def _derive_context(self, hour: int) -> str:
        if hour >= 22 or hour < 6:
            return "Nachtfahrt"
        if 16 <= hour < 20:
            return "Feierabendfahrt"
        if 10 <= hour < 16:
            return "Autobahn"
        return "Stadtverkehr"

    def _get_driving_context(self, hour: int, home_assistant_data: dict[str, str]) -> str:
        driving_context = home_assistant_data.get("driving_context") or home_assistant_data.get("fahrkontext")
        valid_contexts = {"Stadtverkehr", "Autobahn", "Nachtfahrt", "Feierabendfahrt"}
        if driving_context in valid_contexts:
            return str(driving_context)
        return self._derive_context(hour)

    def _get_time_context(self, hour: int, home_assistant_data: dict[str, str]) -> dict[str, str | bool]:
        raw_is_night = home_assistant_data.get("is_night")
        if raw_is_night is not None:
            is_night = str(raw_is_night).strip().lower() in {"1", "true", "ja", "yes"}
            source = "home_assistant"
        elif home_assistant_data.get("time_of_day") in {"day", "night"}:
            is_night = home_assistant_data["time_of_day"] == "night"
            source = "home_assistant"
        else:
            is_night = hour >= 20 or hour < 6
            source = "time_context"

        return {
            "time_of_day": "night" if is_night else "day",
            "is_night": is_night,
            "source": source,
        }

    def _derive_weather(self, hour: int) -> str:
        if hour >= 21 or hour < 6:
            return "Nebel"
        if 6 <= hour < 9:
            return "Regen"
        if 16 <= hour < 19:
            return "Wind"
        return "Klar"

    def _get_weather_context(self, hour: int, home_assistant_data: dict[str, str]) -> str:
        weather = home_assistant_data.get("weather") or home_assistant_data.get("wetter")
        if weather:
            return str(weather)
        return self._derive_weather(hour)

    def _get_critical_maneuver(self, home_assistant_data: dict[str, str]) -> str:
        maneuver = home_assistant_data.get("critical_maneuver") or home_assistant_data.get("criticalManeuver")
        return str(maneuver or "none").strip().lower()

    def _build_weather_sensor(
        self,
        home_assistant_data: dict[str, str],
        outside_temperature: int | None,
    ) -> str:
        base_hint = home_assistant_data.get("hinweis", "Kein Wettersensorstatus")
        if outside_temperature is None:
            return base_hint
        return f"{base_hint} / outside {outside_temperature}C"

    def _derive_route(self, driving_context: str) -> str:
        route_map = {
            "Nachtfahrt": "A8 Urban Exit",
            "Feierabendfahrt": "B27 Ring Approach",
            "Autobahn": "A81 Long Range Corridor",
            "Stadtverkehr": "City Grid Sector West",
        }
        return route_map.get(driving_context, "Porsche Route Mesh")

    def _derive_traffic(self, driving_context: str) -> str:
        traffic_map = {
            "Nachtfahrt": "Moderat",
            "Feierabendfahrt": "Hoch",
            "Autobahn": "Fließend",
            "Stadtverkehr": "Dicht",
        }
        return traffic_map.get(driving_context, "Unbekannt")

    def _derive_camera_status(self, focus_level: int) -> str:
        if focus_level <= 45:
            return "Eyes wandering"
        if focus_level <= 60:
            return "Attention variable"
        return "Eyes on road"

    def _derive_wheel_contact(self, stress_level: int) -> str:
        if stress_level >= 70:
            return "Tense grip"
        if stress_level >= 45:
            return "Controlled"
        return "Stable"

    def _derive_cabin_state(self, stress_level: int) -> str:
        if stress_level >= 70:
            return "Stimulus reduction advised"
        if stress_level >= 45:
            return "Managed load"
        return "Low noise"

    def _build_input_summary(self, driving_context: str, weather: str, risk_score: int) -> str:
        return f"{driving_context} / {weather} / risk {risk_score}"

    def _format_driver_state(self, value: str) -> str:
        labels = {
            "wachsam": "Wachsam",
            "kritisch": "Kritisch",
            "gestresst": "Gestresst",
            "entspannt": "Entspannt",
            "fokussiert": "Fokussiert",
            "muede": "Müde",
            "erschoepft": "Erschöpft",
        }
        return labels.get(value.lower(), value.capitalize())

    def _derive_assist_reaction(self, warning_level: str, focus_level: int, distraction_state: str) -> str:
        has_distraction = distraction_state.strip().lower() != "keine ablenkung"

        if warning_level == "ROT":
            if has_distraction:
                return "Pause + Fokuswarnung"
            return "Interventionslicht / Pause priorisieren"
        if warning_level == "ORANGE":
            if has_distraction or focus_level < 60:
                return "Fokuslenkung"
            return "Wachsamkeitswarnung"
        if warning_level == "GELB":
            if has_distraction or focus_level < 60:
                return "Adaptive Fokus-Hinweise"
            return "Adaptive Wachsamkeitshinweise"
        return "Komforthinweise"

    def _derive_system_mode(self, driver_state: str) -> dict[str, str]:
        normalized = driver_state.strip().lower()
        if normalized == "kritisch":
            return {"label": "Interventionsmodus", "key": "intervention"}
        if normalized == "muede":
            return {"label": "Warnbetrieb", "key": "warning"}
        return {"label": "Normalbetrieb", "key": "normal"}

    def _derive_driving_mode(self, risk_score: int) -> str:
        if risk_score >= 65:
            return "Warnmodus"
        if risk_score >= 35:
            return "Adaptiv"
        return "Komfort"

    def _derive_critical_maneuver_strategy(self, critical_maneuver: str) -> str:
        strategies = {
            "lane_change": "Spiegel pruefen, Schulterblick, Abstand stabil halten",
            "turn": "Abbiegebereich pruefen, Geschwindigkeit reduzieren, Querverkehr beachten",
            "intersection": "Kreuzungsbereich bewusst scannen, Vorfahrt pruefen",
        }
        return strategies.get(critical_maneuver, "")

    def _append_critical_maneuver_strategy(self, text: str, critical_maneuver: str) -> str:
        strategy = self._derive_critical_maneuver_strategy(critical_maneuver)
        if not strategy:
            return text
        return f"{text} {strategy}"

    def _build_ai_summary(self, mode: str, recommendation: str, critical_maneuver: str) -> str:
        enhanced_recommendation = self._append_critical_maneuver_strategy(
            recommendation,
            critical_maneuver,
        )
        return f"System priorisiert {mode.lower()} mit Fokus auf: {enhanced_recommendation}"

    def _derive_warning_title(self, warning_level: str) -> str:
        titles = {
            "ROT": "Immediate Attention",
            "ORANGE": "Elevated Attention",
            "GELB": "Caution Advisory",
            "GRUEN": "Stable Operation",
        }
        return titles.get(warning_level, "Warning State")

    def _derive_warning_priority(self, warning_level: str) -> str:
        priorities = {
            "ROT": "High",
            "ORANGE": "Medium",
            "GELB": "Guarded",
            "GRUEN": "Low",
        }
        return priorities.get(warning_level, "Unknown")

    def _derive_warning_trigger(
        self,
        driving_context: str,
        weather: str,
        energy_level: int,
        stress_level: int,
    ) -> str:
        if driving_context == "Nachtfahrt" and energy_level <= 50:
            return "Night fatigue pattern"
        if weather in {"Regen", "Nebel", "Sturm"} and stress_level >= 60:
            return "Environment stress load"
        if driving_context == "Feierabendfahrt":
            return "Rush-hour strain"
        return "Context adaptation active"

    def _derive_warning_action(
        self,
        warning_level: str,
        recommendation: str,
        critical_maneuver: str,
    ) -> str:
        if warning_level in {"ROT", "ORANGE"}:
            return self._append_critical_maneuver_strategy(recommendation, critical_maneuver)
        return "Monitoring fortsetzen"

    def _capitalize(self, value: str) -> str:
        if not value:
            return value
        return value[0].upper() + value[1:]


class DashboardRequestHandler(BaseHTTPRequestHandler):
    backend = PorscheAssistantBackend()

    def do_GET(self) -> None:
        if self.path == "/api/dashboard-state":
            self._serve_dashboard_state()
            return

        if self.path in STATIC_FILES:
            self._serve_static_file(STATIC_FILES[self.path])
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Resource not found")

    def _serve_dashboard_state(self) -> None:
        payload = self.backend.build_dashboard_state()
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _serve_static_file(self, filename: str) -> None:
        path = BASE_DIR / filename
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Static file missing")
            return

        content_type, _ = mimetypes.guess_type(path.name)
        raw = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type or 'text/plain'}; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, format: str, *args: Any) -> None:
        return


def run_server() -> None:
    server = ThreadingHTTPServer((HOST, PORT), DashboardRequestHandler)
    url = f"http://{HOST}:{PORT}"
    print(f"Porsche Assistance HMI running at {url}")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
