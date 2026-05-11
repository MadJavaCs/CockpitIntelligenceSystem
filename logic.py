import random

VISUAL_STATES = {
    "wachsam": {
        "farbname": "Gruen",
        "hex": "#2ECC71",
    },
    "kritisch": {
        "farbname": "Rot",
        "hex": "#E74C3C",
    },
    "gestresst": {
        "farbname": "Rot",
        "hex": "#E74C3C",
    },
    "entspannt": {
        "farbname": "Gruen",
        "hex": "#2ECC71",
    },
    "fokussiert": {
        "farbname": "Blau",
        "hex": "#3498DB",
    },
    "muede": {
        "farbname": "Gelb",
        "hex": "#F1C40F",
    },
    "erschoepft": {
        "farbname": "Grau",
        "hex": "#95A5A6",
    },
}

BASE_TELEMETRY = {
    "stresslevel": 25,
    "energielevel": 80,
    "fokuslevel": 70,
}


def derive_distraction_state(fokuslevel: int) -> dict[str, str | int]:
    if fokuslevel < 30:
        return {"state": "stark abgelenkt", "risk_modifier": 15}
    if fokuslevel < 60:
        return {"state": "abgelenkt", "risk_modifier": 8}
    return {"state": "keine Ablenkung", "risk_modifier": 0}


def derive_risk_trend(risk_score: int, previous_risk_score: int | None = None) -> str:
    if previous_risk_score is None:
        return "stable"
    delta = risk_score - previous_risk_score
    if delta >= 4:
        return "rising"
    if delta <= -4:
        return "falling"
    return "stable"


def derive_driver_state_from_risk(
    risk_score: int,
    stresslevel: int | None = None,
    energielevel: int | None = None,
    fokuslevel: int | None = None,
    heart_rate_state: str = "normal",
    time_of_day: str | None = None,
    weather: str = "Klar",
    previous_state: str | None = None,
    risk_trend: str = "stable",
) -> str:
    stress = 50 if stresslevel is None else stresslevel
    energy = 60 if energielevel is None else energielevel
    focus = 60 if fokuslevel is None else fokuslevel
    normalized_previous = str(previous_state or "").strip().lower()
    normalized_heart_rate = heart_rate_state.strip().lower()
    normalized_weather = weather.strip().lower()
    is_rising = risk_trend == "rising"
    is_falling = risk_trend == "falling"
    context_pressure = 0

    if stress >= 75:
        context_pressure += 5
    if energy <= 35:
        context_pressure += 5
    if focus <= 40:
        context_pressure += 6
    if normalized_heart_rate == "kritisch erhoeht":
        context_pressure += 8
    elif normalized_heart_rate == "erhoeht":
        context_pressure += 5
    if time_of_day == "night":
        context_pressure += 4
    if normalized_weather == "nebel":
        context_pressure += 4

    effective_risk = clamp_to_percent(risk_score + context_pressure)
    severe_signal = stress >= 82 or focus <= 30 or normalized_heart_rate == "kritisch erhoeht"
    fatigue_signal = energy <= 42 and focus <= 55

    if normalized_previous == "kritisch":
        if risk_score >= 58 or severe_signal or (effective_risk >= 62 and not is_falling):
            return "kritisch"
        return "muede" if risk_score >= 35 or fatigue_signal else "wachsam"

    if normalized_previous == "muede":
        if effective_risk >= 68 and (is_rising or severe_signal):
            return "kritisch"
        if risk_score >= 30 or fatigue_signal or (time_of_day == "night" and normalized_weather == "nebel"):
            return "muede"
        return "wachsam"

    if effective_risk >= 68 and (is_rising or severe_signal or risk_score >= 72):
        return "kritisch"
    if effective_risk >= 38 or fatigue_signal:
        return "muede"
    return "wachsam"


def derive_night_risk_modifier(time_of_day: str | None, energielevel: int, fokuslevel: int) -> int:
    if time_of_day != "night":
        return 0
    if energielevel <= 50 or fokuslevel <= 50:
        return 6
    return 4


def derive_weather_risk_modifier(weather: str, stresslevel: int, fokuslevel: int) -> int:
    normalized_weather = weather.strip().lower()

    if normalized_weather == "sturm":
        return 10
    if normalized_weather == "nebel":
        return 8 if fokuslevel < 60 else 6
    if normalized_weather == "regen":
        return 6 if stresslevel >= 65 else 4
    if normalized_weather == "wind":
        return 3
    return 0


def derive_critical_maneuver_risk_modifier(critical_maneuver: str | None) -> int:
    modifiers = {
        "overtaking": 12,
        "intersection": 9,
        "lane_change": 7,
        "turn": 5,
    }
    return modifiers.get(str(critical_maneuver or "none").strip().lower(), 0)


def derive_heart_rate_risk_modifier(heart_rate: int | None) -> tuple[int, str]:
    if heart_rate is None:
        return 0, "nicht verfuegbar"
    if heart_rate > 105:
        return 15, "kritisch erhoeht"
    if heart_rate >= 86:
        return 8, "erhoeht"
    return 0, "normal"


def derive_awareness_coupling_modifier(heart_rate_state: str, critical_maneuver: str | None) -> int:
    maneuver_modifier = derive_critical_maneuver_risk_modifier(critical_maneuver)
    if maneuver_modifier <= 0:
        return 0
    if heart_rate_state == "kritisch erhoeht":
        return 10 if str(critical_maneuver).strip().lower() in {"turn", "intersection"} else 8
    if heart_rate_state == "erhoeht":
        return 6
    return 0


def derive_support_strategy(
    risk_score: int,
    driver_state: str,
    fokuslevel: int,
    critical_maneuver: str | None = None,
) -> dict[str, str]:
    maneuver_active = derive_critical_maneuver_risk_modifier(critical_maneuver) > 0

    if driver_state == "kritisch" or risk_score >= 65:
        return {
            "support_strategy": "Intervention Support + Maneuver Guard" if maneuver_active else "Intervention Support",
            "assist_reaction": "Intervention Support",
            "trigger_reason": f"Risk {risk_score}: kritischer Zustand",
        }
    if fokuslevel < 60:
        return {
            "support_strategy": "Focus Guidance + Maneuver Guard" if maneuver_active else "Focus Guidance",
            "assist_reaction": "Fokuslenkung",
            "trigger_reason": f"Risk {risk_score}: niedriger Focus",
        }
    if risk_score >= 35:
        return {
            "support_strategy": "Attention Support + Maneuver Guard" if maneuver_active else "Attention Support",
            "assist_reaction": "Wachsamkeitswarnung",
            "trigger_reason": f"Risk {risk_score}: mittlere Belastung",
        }
    return {
        "support_strategy": "Passive Monitoring",
        "assist_reaction": "Monitoring",
        "trigger_reason": f"Risk {risk_score}: stabiler Zustand",
    }


def build_risk_explanation(
    stresslevel: int,
    energielevel: int,
    fokuslevel: int,
    driving_context: str,
    weather: str,
    time_of_day: str | None,
) -> dict[str, str | int | list[dict[str, str | int]]]:
    beitraege: list[dict[str, str | int]] = []

    if time_of_day == "night":
        nacht_beitrag = derive_night_risk_modifier(time_of_day, energielevel, fokuslevel)
        beitraege.append({"label": "Nachtfahrt", "value": nacht_beitrag, "type": "risk"})
    else:
        beitraege.append({"label": "Tagkontext", "value": -1, "type": "stabilizer"})

    if driving_context == "Stadtverkehr":
        beitraege.append({"label": "Stadtverkehr", "value": 3 if stresslevel < 60 else 6, "type": "risk"})
    elif driving_context == "Autobahn":
        beitraege.append({"label": "Autobahn", "value": 2, "type": "risk"})
    elif driving_context == "Nachtfahrt":
        beitraege.append(
            {
                "label": "Nachtfahrt-Kontext",
                "value": 3 if energielevel >= 55 and fokuslevel >= 55 else 4,
                "type": "risk",
            }
        )
    elif driving_context == "Feierabendfahrt":
        beitraege.append({"label": "Feierabendfahrt", "value": 3 if energielevel >= 45 else 7, "type": "risk"})

    weather_delta = derive_weather_risk_modifier(weather, stresslevel, fokuslevel)
    if weather_delta:
        beitraege.append({"label": weather, "value": weather_delta, "type": "risk"})

    stress_delta = 0
    if stresslevel >= 75:
        stress_delta = round((stresslevel - 75) * 0.15)
    elif stresslevel <= 20:
        stress_delta = -round((20 - stresslevel) * 0.08)
    if stress_delta != 0:
        beitraege.append(
            {
                "label": "Stress",
                "value": stress_delta,
                "type": "risk" if stress_delta > 0 else "stabilizer",
            }
        )

    energy_delta = 0
    if energielevel <= 35:
        energy_delta = round((35 - energielevel) * 0.12)
    elif energielevel >= 85:
        energy_delta = -round((energielevel - 85) * 0.08)
    if energy_delta != 0:
        beitraege.append(
            {
                "label": "Energy",
                "value": energy_delta,
                "type": "risk" if energy_delta > 0 else "stabilizer",
            }
        )

    focus_delta = 0
    if fokuslevel <= 35:
        focus_delta = round((35 - fokuslevel) * 0.10)
    elif fokuslevel >= 85:
        focus_delta = -round((fokuslevel - 85) * 0.07)
    if focus_delta != 0:
        beitraege.append(
            {
                "label": "Focus",
                "value": focus_delta,
                "type": "risk" if focus_delta > 0 else "stabilizer",
            }
        )

    ablenkung = derive_distraction_state(fokuslevel)
    if int(ablenkung["risk_modifier"]) > 0:
        beitraege.append(
            {
                "label": f'Ablenkung ({ablenkung["state"]})',
                "value": int(ablenkung["risk_modifier"]),
                "type": "risk",
            }
        )

    treiber: list[str] = []
    stabilisierer: list[str] = []

    if time_of_day == "night":
        treiber.append("Nachtfahrt")
    else:
        stabilisierer.append("Tagkontext")

    if weather == "Sturm":
        treiber.append("Sturm")
    elif weather == "Nebel":
        treiber.append("Nebel")
    elif weather == "Regen":
        treiber.append("Regen")
    elif weather == "Wind":
        treiber.append("Wind")

    if stresslevel >= 70:
        treiber.append("hoher Stress")
    elif stresslevel <= 20:
        stabilisierer.append("niedriger Stress")

    if energielevel <= 35:
        treiber.append("niedrige Energy")
    elif energielevel >= 85:
        stabilisierer.append("hohe Energy")

    if fokuslevel <= 35:
        treiber.append("niedriger Focus")
    elif fokuslevel >= 85:
        stabilisierer.append("hoher Focus")

    if str(ablenkung["state"]) != "keine Ablenkung":
        treiber.append(str(ablenkung["state"]))

    if treiber:
        teile = " + ".join(treiber[:3])
        verb = "erhoeht" if len(treiber) == 1 else "erhoehen"
        summary = f"{teile} {verb} das Risiko."
    else:
        teile = " + ".join(stabilisierer[:3] or ["Ausgeglichene Werte"])
        verb = "stabilisiert" if " + " not in teile else "stabilisieren"
        summary = f"{teile} {verb} den Zustand."

    top_drivers = [
        beitrag["label"]
        for beitrag in sorted(
            (item for item in beitraege if int(item["value"]) > 0),
            key=lambda item: int(item["value"]),
            reverse=True,
        )[:3]
    ]
    detail_lines = [
        f'{beitrag["label"]} {int(beitrag["value"]):+d}'
        for beitrag in sorted(beitraege, key=lambda item: abs(int(item["value"])), reverse=True)[:4]
        if int(beitrag["value"]) != 0
    ]

    return {
        "summary": summary,
        "top_drivers": top_drivers,
        "contributions": beitraege,
        "detail_text": " | ".join(detail_lines),
    }


def build_risk_formula(
    stresslevel: int,
    energielevel: int,
    fokuslevel: int,
    weather: str = "Klar",
    time_of_day: str | None = None,
    critical_maneuver: str | None = None,
    heart_rate: int | None = None,
    random_offset: int | None = None,
) -> dict[str, str | int | float]:
    stress_component = round(stresslevel * 0.45, 1)
    energy_component = round((100 - energielevel) * 0.35, 1)
    focus_component = round((100 - fokuslevel) * 0.20, 1)
    distraction = derive_distraction_state(fokuslevel)
    distraction_modifier = int(distraction["risk_modifier"])
    night_modifier = derive_night_risk_modifier(time_of_day, energielevel, fokuslevel)
    weather_modifier = derive_weather_risk_modifier(weather, stresslevel, fokuslevel)
    maneuver_modifier = derive_critical_maneuver_risk_modifier(critical_maneuver)
    heart_rate_modifier, heart_rate_state = derive_heart_rate_risk_modifier(heart_rate)
    awareness_modifier = derive_awareness_coupling_modifier(heart_rate_state, critical_maneuver)
    offset = random.randint(-5, 5) if random_offset is None else max(-5, min(5, int(random_offset)))
    score = clamp_to_percent(
        round(
            stress_component
            + energy_component
            + focus_component
            + distraction_modifier
            + night_modifier
            + weather_modifier
            + maneuver_modifier
            + heart_rate_modifier
            + awareness_modifier
            + offset
        )
    )

    return {
        "score": score,
        "stress_component": stress_component,
        "energy_component": energy_component,
        "focus_component": focus_component,
        "distraction_state": str(distraction["state"]),
        "distraction_modifier": distraction_modifier,
        "night_modifier": night_modifier,
        "weather_modifier": weather_modifier,
        "critical_maneuver_modifier": maneuver_modifier,
        "heart_rate_modifier": heart_rate_modifier,
        "heart_rate_state": heart_rate_state,
        "awareness_coupling_modifier": awareness_modifier,
        "random_offset": offset,
        "formula_text": (
            f"Stress {stress_component:.1f} + Energy {energy_component:.1f} + "
            f"Focus {focus_component:.1f} + Ablenkung {distraction_modifier:+d} "
            f"+ Nacht {night_modifier:+d} + Wetter {weather_modifier:+d} "
            f"+ Manoever {maneuver_modifier:+d} + Herzfrequenz {heart_rate_modifier:+d} "
            f"+ Kopplung {awareness_modifier:+d} + Zufall {offset:+d}"
        ),
    }


def calculate_telemetry(
    uhrzeit: str,
    driving_context: str,
    weather: str = "Klar",
    outside_temperature: int | None = None,
) -> dict[str, int]:
    werte = dict(BASE_TELEMETRY)
    stunde = parse_stunde(uhrzeit)
    tagesphase = get_tagesphase(stunde)

    if driving_context == "Stadtverkehr":
        werte["stresslevel"] += 18
        werte["fokuslevel"] += 3
    elif driving_context == "Autobahn":
        werte["stresslevel"] += 4
        werte["fokuslevel"] -= 10
    elif driving_context == "Nachtfahrt":
        werte["stresslevel"] += 5
        werte["energielevel"] -= 18
        werte["fokuslevel"] -= 18
    elif driving_context == "Feierabendfahrt":
        werte["stresslevel"] += 10
        werte["energielevel"] -= 10

    if tagesphase == "day":
        werte["energielevel"] += 5
    else:
        werte["stresslevel"] += 5
        werte["energielevel"] -= 15
        werte["fokuslevel"] -= 12

    if driving_context == "Autobahn" and tagesphase == "night":
        werte["fokuslevel"] -= 6

    if driving_context == "Stadtverkehr" and tagesphase == "night":
        werte["stresslevel"] += 4

    if weather == "Regen":
        werte["stresslevel"] += 6
        werte["fokuslevel"] -= 4
    elif weather == "Wind":
        werte["stresslevel"] += 4
        werte["fokuslevel"] -= 2
    elif weather == "Nebel":
        werte["stresslevel"] += 8
        werte["energielevel"] -= 3
        werte["fokuslevel"] -= 8
    elif weather == "Sturm":
        werte["stresslevel"] += 12
        werte["energielevel"] -= 6
        werte["fokuslevel"] -= 10

    if weather in {"Regen", "Nebel", "Sturm"} and driving_context == "Stadtverkehr":
        werte["stresslevel"] += 6

    if weather in {"Wind", "Sturm"} and driving_context == "Autobahn":
        werte["stresslevel"] += 5
        werte["fokuslevel"] -= 3

    if outside_temperature is not None:
        if outside_temperature <= 3:
            werte["stresslevel"] += 4
            werte["energielevel"] -= 3
        elif outside_temperature >= 30:
            werte["stresslevel"] += 5
            werte["fokuslevel"] -= 4

    return {schluessel: clamp_to_percent(wert) for schluessel, wert in werte.items()}


def evaluate_context(
    uhrzeit: str,
    stresslevel: int,
    energielevel: int,
    fokuslevel: int,
    driving_context: str,
    weather: str = "Klar",
    outside_temperature: int | None = None,
) -> dict[str, str]:
    stunde = parse_stunde(uhrzeit)
    time_of_day = get_tagesphase(stunde)

    if driving_context == "Stadtverkehr" and weather in {"Regen", "Nebel", "Sturm"} and stresslevel >= 70:
        mentaler_zustand = "gestresst"
        modus = "Schutzmodus"
        empfehlung = "Abstand vergroessern, Tempo ruhig halten und Ablenkungen konsequent reduzieren"
        begruendung = "Dichter Stadtverkehr bei schwierigem Wetter fuehrt zu hoher mentaler Last und verlangt besonders ruhige Unterstuetzung."
    elif driving_context == "Stadtverkehr" and stresslevel >= 70:
        mentaler_zustand = "gestresst"
        modus = "Ruhiger Modus"
        empfehlung = "Reize reduzieren, Fahrhinweise klar halten und ruhig fahren"
        begruendung = "Stadtverkehr mit hohem Stress spricht fuer Reizreduktion und Entlastung."
    elif driving_context == "Autobahn" and weather in {"Wind", "Sturm"} and (stresslevel >= 50 or fokuslevel <= 45):
        mentaler_zustand = "gestresst"
        modus = "Stabilisierung"
        empfehlung = "Lenkkorrekturen ruhig ausfuehren und Spurhaltung priorisieren"
        begruendung = "Autobahn bei Wind oder Sturm erfordert dauerhafte Korrekturen und bindet Aufmerksamkeit."
    elif driving_context == "Autobahn" and energielevel <= 35:
        mentaler_zustand = "muede"
        modus = "Warnmodus"
        empfehlung = "Konzentration sichern, Pause pruefen und bei Bedarf Kaffee einplanen"
        begruendung = "Autobahn und niedrige Energie erhoehen das Risiko fuer nachlassende Aufmerksamkeit."
    elif driving_context == "Autobahn" and fokuslevel <= 45 and energielevel <= 60:
        mentaler_zustand = "muede"
        modus = "Aktivierung"
        empfehlung = "Monotonie unterbrechen, Fahrpause vorbereiten und Aufmerksamkeit aktiv halten"
        begruendung = "Auf der Autobahn sinkt der Fokus schleichend. In Verbindung mit mittlerer Energie entsteht ein realistisches Monotonierisiko."
    elif driving_context == "Feierabendfahrt" and energielevel <= 30:
        mentaler_zustand = "erschoepft"
        modus = "Relax"
        empfehlung = "Belastung senken, ruhig fahren und moeglichst bald Erholung einplanen"
        begruendung = "Feierabendfahrt mit hoher Erschoepfung spricht fuer einen besonders entlastenden Modus."
    elif driving_context == "Nachtfahrt" and energielevel <= 45:
        mentaler_zustand = "muede"
        modus = "Wachsamkeit"
        empfehlung = "Aufmerksamkeit aktiv halten und bei ersten Ermuedungszeichen Pause machen"
        begruendung = "Nachtfahrt mit sinkender Energie verlangt eine vorsichtige, wachsamkeitsorientierte Begleitung."
    elif stresslevel >= 80:
        mentaler_zustand = "gestresst"
        modus = "Entlastung"
        empfehlung = "Ruhe schaffen und kurze Pause einplanen"
        begruendung = "Das Stresslevel ist sehr hoch und ueberlagert die anderen Werte."
    elif energielevel <= 20:
        mentaler_zustand = "erschoepft"
        modus = "Erholung"
        empfehlung = "Belastung reduzieren und Regeneration einplanen"
        begruendung = "Das Energielevel ist sehr niedrig und spricht fuer deutlichen Erholungsbedarf."
    elif energielevel <= 40 and fokuslevel <= 40:
        mentaler_zustand = "muede"
        modus = "Schonung"
        empfehlung = "Mit einfachen Aufgaben starten und das Tempo reduzieren"
        begruendung = "Niedrige Energie und niedriger Fokus deuten auf Muedigkeit hin."
    elif outside_temperature is not None and outside_temperature >= 30 and stresslevel >= 60:
        mentaler_zustand = "gestresst"
        modus = "Entlastung"
        empfehlung = "Innenraumtemperatur senken und Reizlast ruhig halten"
        begruendung = "Hohe Aussentemperatur und steigender Stress sprechen fuer eine entlastende Assistenz."
    elif outside_temperature is not None and outside_temperature <= 3 and energielevel <= 55:
        mentaler_zustand = "muede"
        modus = "Wachsamkeit"
        empfehlung = "Kaelte beachten, Aufmerksamkeit sichern und Ermuedung frueh ausgleichen"
        begruendung = "Niedrige Aussentemperatur und sinkende Energie belasten die Wachheit zusaetzlich."
    elif time_of_day == "night" and energielevel <= 50 and fokuslevel <= 50:
        mentaler_zustand = "muede"
        modus = "Wachsamkeit"
        empfehlung = "Fahrumgebung aktiv beobachten und fruehzeitig eine Pause einplanen"
        begruendung = "Nachts fallen Energie und Fokus typischerweise gemeinsam ab. Der Zustand bleibt noch kontrollierbar, ist aber klar ermuedungsnah."
    elif fokuslevel >= 70 and stresslevel <= 40:
        mentaler_zustand = "fokussiert"
        modus = "Produktiv"
        empfehlung = "Wichtige Aufgaben jetzt konzentriert bearbeiten"
        begruendung = "Hoher Fokus und niedriger Stress sprechen fuer eine produktive Phase."
    elif 5 <= stunde < 12 and energielevel >= 60 and fokuslevel >= 50:
        mentaler_zustand = "fokussiert"
        modus = "Produktiv"
        empfehlung = "Den Vormittag fuer anspruchsvolle Aufgaben nutzen"
        begruendung = "Tageszeit, Energie und Fokus unterstuetzen konzentriertes Arbeiten."
    else:
        mentaler_zustand = "entspannt"
        modus = "Ausgleich"
        empfehlung = "Ruhig weiterfahren und den naechsten Schritt bewusst planen"
        begruendung = "Die Werte zeigen eine stabile Situation ohne akuten Handlungsdruck."

    if time_of_day == "night" and mentaler_zustand in {"entspannt", "fokussiert"}:
        empfehlung = "Nachts Aufmerksamkeit etwas hoeher halten und Ermuedung frueh beobachten"
        begruendung = "Die Lage ist stabil, nachts sollte das System dennoch vorsichtiger begleiten."

    kaffee = entscheide_kaffee(
        mentaler_zustand,
        stresslevel,
        energielevel,
        fokuslevel,
        driving_context,
        weather,
    )

    return {
        "mentaler_zustand": mentaler_zustand,
        "modus": modus,
        "empfehlung": empfehlung,
        "begruendung": begruendung,
        "coffee_recommendation": kaffee["coffee_recommendation"],
        "coffee_reason": kaffee["coffee_reason"],
    }


def analyze_driver_state(
    uhrzeit: str,
    driving_context: str,
    weather: str = "Klar",
    outside_temperature: int | None = None,
    critical_maneuver: str | None = None,
    heart_rate: int | None = None,
    previous_state: str | None = None,
    previous_risk_score: int | None = None,
) -> dict[str, dict[str, str | int]]:
    time_of_day = get_time_of_day(uhrzeit)
    is_night = time_of_day == "night"
    telemetrie = calculate_telemetry(uhrzeit, driving_context, weather, outside_temperature)
    risikologik = build_risk_formula(
        telemetrie["stresslevel"],
        telemetrie["energielevel"],
        telemetrie["fokuslevel"],
        weather,
        time_of_day,
        critical_maneuver,
        heart_rate,
    )
    auswertung = evaluate_context(
        uhrzeit,
        telemetrie["stresslevel"],
        telemetrie["energielevel"],
        telemetrie["fokuslevel"],
        driving_context,
        weather,
        outside_temperature,
    )
    risikoscore = int(risikologik["score"])
    risiko_trend = derive_risk_trend(risikoscore, previous_risk_score)
    fahrerzustand = derive_driver_state_from_risk(
        risikoscore,
        telemetrie["stresslevel"],
        telemetrie["energielevel"],
        telemetrie["fokuslevel"],
        str(risikologik["heart_rate_state"]),
        time_of_day,
        weather,
        previous_state,
        risiko_trend,
    )
    risiko_begruendung = build_risk_explanation(
        telemetrie["stresslevel"],
        telemetrie["energielevel"],
        telemetrie["fokuslevel"],
        driving_context,
        weather,
        time_of_day,
    )
    warnstufe = determine_warning_level(risikoscore)
    lichtmodus = determine_light_mode(fahrerzustand, warnstufe)
    lichtfarbe = get_visual_state(fahrerzustand)
    support = derive_support_strategy(risikoscore, fahrerzustand, telemetrie["fokuslevel"], critical_maneuver)

    return {
        "input": {
            "uhrzeit": uhrzeit,
            "kontext": driving_context,
            "wetter": weather,
        },
        "system_context": {
            "time_of_day": time_of_day,
            "is_night": is_night,
        },
        "telemetry": telemetrie,
        "assessment": {
            "fahrerzustand": fahrerzustand,
            "risiko_score": risikoscore,
            "risiko_formel": str(risikologik["formula_text"]),
            "distraction_state": str(risikologik["distraction_state"]),
            "distraction_modifier": int(risikologik["distraction_modifier"]),
            "night_modifier": int(risikologik["night_modifier"]),
            "weather_modifier": int(risikologik["weather_modifier"]),
            "critical_maneuver_modifier": int(risikologik["critical_maneuver_modifier"]),
            "heart_rate_modifier": int(risikologik["heart_rate_modifier"]),
            "awareness_coupling_modifier": int(risikologik["awareness_coupling_modifier"]),
            "risiko_random_offset": int(risikologik["random_offset"]),
            "risiko_trend": risiko_trend,
            "warnstufe": warnstufe,
            "empfehlung": auswertung["empfehlung"],
            "begruendung": auswertung["begruendung"],
            "risiko_begruendung": risiko_begruendung["summary"],
            "risiko_treiber": risiko_begruendung["top_drivers"],
            "risiko_beitraege": risiko_begruendung["contributions"],
            "risiko_details": risiko_begruendung["detail_text"],
            "modus": auswertung["modus"],
            "support_strategy": support["support_strategy"],
            "trigger_reason": support["trigger_reason"],
            "assist_reaction": support["assist_reaction"],
            "lichtmodus": lichtmodus,
            "lichtfarbe": lichtfarbe["farbname"],
            "lichtfarbe_hex": lichtfarbe["hex"],
            "coffee_recommendation": auswertung["coffee_recommendation"],
            "coffee_reason": auswertung["coffee_reason"],
        },
    }


def entscheide_kaffee(
    mentaler_zustand: str,
    stresslevel: int,
    energielevel: int,
    fokuslevel: int,
    driving_context: str,
    weather: str = "Klar",
) -> dict[str, str]:
    if driving_context == "Stadtverkehr" and weather in {"Regen", "Nebel", "Sturm"} and stresslevel >= 70:
        return {
            "coffee_recommendation": "nicht empfohlen",
            "coffee_reason": "Stadtverkehr bei schwierigem Wetter erzeugt bereits hohe Aktivierung. Mehr Stimulation wuerde eher belasten als helfen.",
        }

    if driving_context == "Stadtverkehr" and stresslevel >= 70:
        return {
            "coffee_recommendation": "nicht empfohlen",
            "coffee_reason": "Im Stadtverkehr ist das Stressniveau bereits hoch. Reizreduktion und ruhige Fahrfuehrung sind hier sinnvoller als zusaetzliche Stimulation.",
        }

    if stresslevel >= 80:
        return {
            "coffee_recommendation": "nicht empfohlen",
            "coffee_reason": "Das Stresslevel ist sehr hoch. Kaffee wuerde die Aktivierung eher weiter erhoehen als sinnvoll entlasten.",
        }

    if driving_context == "Autobahn" and weather in {"Wind", "Sturm"} and stresslevel >= 65:
        return {
            "coffee_recommendation": "nicht empfohlen",
            "coffee_reason": "Bei Wind oder Sturm auf der Autobahn ist die Belastung bereits hoch. Ruhe und defensive Fahrweise helfen mehr als weitere Aktivierung.",
        }

    if driving_context == "Autobahn" and energielevel <= 30:
        return {
            "coffee_recommendation": "empfohlen",
            "coffee_reason": "Autobahnfahrt bei sehr niedriger Energie spricht fuer einen klaren Wachheitsbedarf. Kaffee oder eine zeitnahe Pause sind in dieser Situation sinnvoll.",
        }

    if driving_context == "Nachtfahrt" and energielevel <= 35:
        return {
            "coffee_recommendation": "empfohlen",
            "coffee_reason": "Nachtfahrt und niedrige Energie deuten auf sinkende Wachsamkeit hin. Kaffee kann unterstuetzen, eine Pause bleibt aber die sicherere Ergaenzung.",
        }

    if driving_context == "Autobahn" and energielevel <= 45 and fokuslevel <= 55:
        return {
            "coffee_recommendation": "empfohlen",
            "coffee_reason": "Auf der Autobahn treffen reduzierte Energie und nachlassender Fokus zusammen. Kaffee ist hier als Aktivierung gut begruendbar.",
        }

    if driving_context == "Feierabendfahrt" and 35 <= energielevel <= 60 and stresslevel <= 65:
        return {
            "coffee_recommendation": "optional",
            "coffee_reason": "Bei der Feierabendfahrt ist etwas Ermuedung erkennbar, aber keine akute Unterversorgung. Kaffee ist moeglich, eine ruhige Weiterfahrt ist jedoch ebenfalls passend.",
        }

    if energielevel <= 30 and stresslevel <= 55:
        return {
            "coffee_recommendation": "empfohlen",
            "coffee_reason": "Die Energie ist deutlich reduziert, waehrend das Stressniveau noch kontrollierbar bleibt. Kaffee kann die Aktivierung sinnvoll stuetzen.",
        }

    if energielevel <= 50 and fokuslevel <= 55 and stresslevel <= 70:
        return {
            "coffee_recommendation": "optional",
            "coffee_reason": "Energie und Fokus liegen im mittleren bis niedrigen Bereich. Kaffee kann helfen, ist aber nicht zwingend notwendig.",
        }

    if mentaler_zustand in {"muede", "erschoepft"} and stresslevel <= 60:
        return {
            "coffee_recommendation": "optional",
            "coffee_reason": "Der Fahrerzustand zeigt Ermuedung, jedoch ohne starkes Stresssignal. Kaffee ist moeglich, sollte aber nicht Pausen oder Erholung ersetzen.",
        }

    return {
        "coffee_recommendation": "nicht empfohlen",
        "coffee_reason": "Die aktuelle Kombination aus Energie, Fokus, Stress und Fahrkontext liefert keinen klaren Zusatznutzen fuer Kaffee.",
    }


def calculate_risk_score(
    stresslevel: int,
    energielevel: int,
    fokuslevel: int,
    driving_context: str,
    weather: str = "Klar",
    time_of_day: str | None = None,
    outside_temperature: int | None = None,
) -> int:
    return int(build_risk_formula(stresslevel, energielevel, fokuslevel, weather, time_of_day)["score"])


def determine_warning_level(risk_score: int) -> str:
    if risk_score >= 80:
        return "ROT"
    if risk_score >= 60:
        return "ORANGE"
    if risk_score >= 35:
        return "GELB"
    return "GRUEN"


def determine_light_mode(mental_state: str, warning_level: str) -> str:
    if warning_level == "ROT":
        return "Interventionslicht"
    if warning_level == "ORANGE":
        return "Warnlicht"
    if mental_state == "wachsam":
        return "Komfortlicht"
    if mental_state == "fokussiert":
        return "Fokuslicht"
    if mental_state == "entspannt":
        return "Komfortlicht"
    if mental_state in {"muede", "erschoepft", "kritisch"}:
        return "Aktivierungslicht"
    return "Adaptivlicht"


def get_visual_state(mental_state: str) -> dict[str, str]:
    schluessel = mental_state.strip().lower()

    return VISUAL_STATES.get(
        schluessel,
        {
            "farbname": "Neutral",
            "hex": "#BDC3C7",
        },
    )


def parse_stunde(uhrzeit: str) -> int:
    teile = uhrzeit.split(":")
    stunde = int(teile[0])

    if stunde < 0 or stunde > 23:
        raise ValueError("Die Uhrzeit muss zwischen 00:00 und 23:59 liegen.")

    return stunde


def get_tagesphase(stunde: int) -> str:
    if 6 <= stunde < 20:
        return "day"
    return "night"


def get_time_of_day(uhrzeit: str) -> str:
    return get_tagesphase(parse_stunde(uhrzeit))


def clamp_to_percent(wert: int) -> int:
    return max(0, min(100, int(wert)))
