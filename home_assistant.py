from __future__ import annotations

from datetime import datetime

class HomeAssistantClient:
    def get_context_data(self) -> dict[str, str]:
        now = datetime.now()
        is_night = now.hour >= 20 or now.hour < 6

        return {
            "uhrzeit": now.strftime("%H:%M"),
            "time_of_day": "night" if is_night else "day",
            "is_night": "true" if is_night else "false",
            "kalenderstatus": "Nächster Termin um 10:00 Uhr",
            "geraetestatus": "Wohnzimmerlicht eingeschaltet",
            "fahrkontext": "Nachtfahrt" if is_night else "Stadtverkehr",
            "wetter": "Nebel" if is_night else "Regen",
            "outside_temperature": "8" if is_night else "14",
            "hinweis": "Beispieldaten aus der vorbereiteten Home-Assistant-Schnittstelle",
        }


def get_home_assistant_data() -> dict[str, str]:
    return HomeAssistantClient().get_context_data()
