import importlib.util
import tkinter as tk
from tkinter import messagebox, ttk

from logic import calculate_telemetry, evaluate_context, get_visual_state


DRIVING_CONTEXTS = [
    "Stadtverkehr",
    "Autobahn",
    "Feierabendfahrt",
    "Nachtfahrt",
]

WEATHER_CONDITIONS = [
    "Klar",
    "Regen",
    "Wind",
    "Nebel",
    "Sturm",
]


PALETTE = {
    "bg": "#050912",
    "bg_secondary": "#09111C",
    "panel": "#0E1827",
    "panel_alt": "#132236",
    "panel_deep": "#09101A",
    "panel_border": "#1D324B",
    "grid": "#10314A",
    "grid_soft": "#0B2435",
    "scanline": "#0B2030",
    "panel_glow": "#36E0FF",
    "text": "#F0F8FF",
    "muted": "#7E98B3",
    "cyan": "#36E0FF",
    "amber": "#FFA31A",
    "danger": "#FF4D6D",
    "violet": "#A87BFF",
    "lime": "#A6FF47",
    "entry_bg": "#08101A",
    "track": "#060C14",
}

STATE_UI_ACCENTS = {
    "gestresst": {"accent": PALETTE["danger"], "surface": "#2A1119", "badge": "THREAT HIGH"},
    "entspannt": {"accent": PALETTE["cyan"], "surface": "#112637", "badge": "STABLE"},
    "fokussiert": {"accent": PALETTE["cyan"], "surface": "#0F2843", "badge": "TARGET LOCK"},
    "muede": {"accent": PALETTE["amber"], "surface": "#35240F", "badge": "FATIGUE"},
    "erschoepft": {"accent": PALETTE["violet"], "surface": "#24192F", "badge": "RECOVERY"},
}

WARNING_COLORS = {
    "GRUEN": "Gruen",
    "GELB": "Gelb",
    "ORANGE": "Orange",
    "ROT": "Rot",
}

DISPLAY_DRIVER_STATES = {
    "gestresst": "Hohe mentale Last",
    "entspannt": "Stabile Ausgleichslage",
    "fokussiert": "Stabile Fokuslage",
    "muede": "Reduzierte Wachheit",
    "erschoepft": "Niedrige Energiereserve",
}

DISPLAY_MODES = {
    "Schutzmodus": "Assistenzprofil Schutz",
    "Ruhiger Modus": "Assistenzprofil Beruhigung",
    "Stabilisierung": "Assistenzprofil Stabilisierung",
    "Warnmodus": "Assistenzprofil Warnung",
    "Aktivierung": "Assistenzprofil Aktivierung",
    "Relax": "Assistenzprofil Entlastung",
    "Wachsamkeit": "Assistenzprofil Wachsamkeit",
    "Entlastung": "Assistenzprofil Entlastung",
    "Erholung": "Assistenzprofil Regeneration",
    "Schonung": "Assistenzprofil Schonung",
    "Produktiv": "Assistenzprofil Fokus",
    "Ausgleich": "Assistenzprofil Balance",
}


def _cli_divider(width: int = 72, char: str = "=") -> str:
    return char * width


def _cli_status_line(label: str, value: object, width: int = 76) -> str:
    content = f"{label}: {value}"
    return content[:width]


def _cli_meter(value: int, width: int = 20) -> str:
    filled = max(0, min(width, round((value / 100) * width)))
    empty = width - filled
    return f"[{'#' * filled}{'.' * empty}] {value:03d}/100"


def _cli_box(lines: list[str], width: int = 72) -> None:
    inner_width = width - 4
    print("+" + "-" * (width - 2) + "+")
    for line in lines:
        print(f"| {line[:inner_width]:<{inner_width}} |")
    print("+" + "-" * (width - 2) + "+")


def _cli_title(text: str) -> None:
    print()
    _cli_box([text.upper()], width=44)


def _cli_field(label: str, value: object) -> None:
    print(f"  {label:<20} {value}")


def _format_warning_stage(warnstufe: str) -> str:
    return f"{warnstufe} / {WARNING_COLORS.get(str(warnstufe), 'Unbekannt')}"


def _display_driver_state(zustand: str) -> str:
    return DISPLAY_DRIVER_STATES.get(zustand, zustand)


def _display_mode(modus: str) -> str:
    return DISPLAY_MODES.get(modus, modus)


def _format_risk_band(risiko_score: int) -> str:
    if risiko_score >= 80:
        return "kritisch"
    if risiko_score >= 60:
        return "erhoeht"
    if risiko_score >= 35:
        return "beobachten"
    return "stabil"


def _build_context_summary(eingabe: dict[str, str], telemetrie: dict[str, int]) -> str:
    return (
        f"Fahrprofil {eingabe['kontext']}, Witterung {eingabe['wetter']}, Uhrzeit {eingabe['uhrzeit']}, "
        f"Belastung {telemetrie['stresslevel']}/100, Energie {telemetrie['energielevel']}/100, "
        f"Aufmerksamkeitsfokus {telemetrie['fokuslevel']}/100."
    )


def _build_system_reaction(bewertung: dict[str, str | int]) -> str:
    warnstufe = str(bewertung["warnstufe"])
    if warnstufe == "ROT":
        return "Intervention priorisieren, Hinweisfrequenz erhoehen und Cockpitreize konsequent beruhigen."
    if warnstufe == "ORANGE":
        return "Assistenzpraesenz anheben, Fahrerfokus aktiv stuetzen und Lichtfuehrung klar verdichten."
    if warnstufe == "GELB":
        return "System bleibt praeventiv, setzt fruehe Hinweise und justiert die Ambientefuehrung moderat."
    return "System verbleibt im adaptiven Begleitmodus ohne unmittelbaren Interventionseingriff."


def _build_warning_marker(warnstufe: str) -> str:
    markers = {
        "GRUEN": "[STATUS NOMINAL]",
        "GELB": "[STATUS ADVISORY]",
        "ORANGE": "[STATUS CAUTION]",
        "ROT": "[STATUS CRITICAL]",
    }
    return markers.get(warnstufe, "[STATUS UNKNOWN]")


def _build_driver_impression(zustand: str, risiko_score: int) -> str:
    if zustand == "gestresst":
        return "Erhoehte mentale Last, Reizreduktion und stabile Fuehrung priorisieren."
    if zustand == "muede":
        return "Nachlassende Wachheit, Aufmerksamkeitsbindung aktiv absichern."
    if zustand == "erschoepft":
        return "Deutlich reduzierte Reserve, entlastende Fahrzeuglogik bevorzugen."
    if zustand == "fokussiert" and risiko_score < 35:
        return "Stabile Leistungsbereitschaft bei kontrolliertem Risikobild."
    return "Ausgeglichener Zustand ohne akuten Interventionsdruck."


def show_cli_title() -> None:
    print()
    _cli_box(
        [
            "PORSCHE ASSISTANT",
            "Systemlauf fuer Fahrerzustand, Risikobild und adaptive Assistenzreaktion",
            "",
            "Systemstart abgeschlossen. Analysezyklus wird vorbereitet.",
        ]
    )


def show_main_menu() -> None:
    print()
    _cli_box(
        [
            "COCKPIT MODI",
            "",
            "[1] Live-Diagnose mit manueller Dateneingabe",
            "[2] Referenzfahrt zur Systemdemonstration",
            "[3] Sitzung beenden",
            "",
            "Auswahl ueber Eingabekonsole.",
        ]
    )


def show_section(title: str) -> None:
    _cli_title(title)


def show_analysis_result(
    context: dict[str, str],
    driver_state: dict[str, str | int],
    result: dict[str, dict[str, str | int]],
) -> None:
    eingabe = result["input"]
    telemetrie = result["telemetry"]
    bewertung = result["assessment"]
    systemkontext = result.get("system_context", {})
    risiko_score = int(bewertung["risiko_score"])
    systemreaktion = _build_system_reaction(bewertung)
    kontextbericht = _build_context_summary(eingabe, telemetrie)
    warnmarker = _build_warning_marker(str(bewertung["warnstufe"]))
    fahrereindruck = _build_driver_impression(str(bewertung["fahrerzustand"]), risiko_score)
    fahrerzustand_anzeige = _display_driver_state(str(bewertung["fahrerzustand"]))
    assistenzmodus_anzeige = _display_mode(str(bewertung["modus"]))

    print()
    _cli_box(
        [
            "PORSCHE SYSTEM REPORT",
            "",
            "Analyse, Risikobewertung und Assistenzempfehlung wurden abgeschlossen.",
            warnmarker,
        ],
        width=86,
    )

    show_section("KONTEXT")
    _cli_field("Systemstatus", systemkontext.get("systemstatus", "ONLINE"))
    _cli_field("Betriebsphase", systemkontext.get("betriebsphase", "Unbekannt"))
    _cli_field("Ablaufmodus", systemkontext.get("override_mode", "STANDARD"))
    _cli_field("Fahrkontext", context.get("kontext", eingabe["kontext"]))
    _cli_field("Witterung", context.get("wetter", eingabe["wetter"]))
    _cli_field("Zeitstempel", context.get("uhrzeit", eingabe["uhrzeit"]))
    _cli_field("Wettersensor", systemkontext.get("wettersensor", "Dummy-Sensor nominal"))
    _cli_field("Kalenderstatus", systemkontext.get("kalenderstatus", "Keine Kalenderdaten"))
    _cli_field("Geraetestatus", systemkontext.get("geraetestatus", "Keine Geraetedaten"))
    _cli_field("Zusatzhinweis", systemkontext.get("hinweis", "Kein Hinweis"))

    show_section("FAHRERZUSTAND")
    _cli_field("Kontextzusammenfassung", kontextbericht)
    _cli_field("Belastungsindex", _cli_meter(int(driver_state.get("stresslevel", telemetrie["stresslevel"]))))
    _cli_field("Energiereserve", _cli_meter(int(driver_state.get("energielevel", telemetrie["energielevel"]))))
    _cli_field("Fokusstabilitaet", _cli_meter(int(driver_state.get("fokuslevel", telemetrie["fokuslevel"]))))
    _cli_field("Erkannter Zustand", _display_driver_state(str(driver_state.get("fahrerzustand", bewertung["fahrerzustand"]))))
    _cli_field("Systemeinschaetzung", fahrereindruck)

    show_section("BEWERTUNG")
    _cli_field("Erkannter Fahrerzustand", fahrerzustand_anzeige)
    _cli_field("Aktiver Assistenzmodus", assistenzmodus_anzeige)
    _cli_field("Risiko-Score", f"{risiko_score} / 100 ({_format_risk_band(risiko_score)})")
    _cli_field("Warnstufe", _format_warning_stage(str(bewertung["warnstufe"])))
    _cli_field("Empfohlener Lichtmodus", bewertung["lichtmodus"])
    _cli_field("Ambientesignal", f"{bewertung['lichtfarbe']} / {bewertung['lichtfarbe_hex']}")

    show_section("EMPFEHLUNG")
    _cli_field("Empfohlene Fahreraktion", bewertung["empfehlung"])
    _cli_field("Assistenzreaktion", systemreaktion)
    _cli_field("Bewertungsgrundlage", driver_state.get("begruendung", bewertung["begruendung"]))
    _cli_field("Wachheitsimpuls", bewertung["coffee_recommendation"])
    _cli_field("Impulsbegruendung", bewertung["coffee_reason"])

    print()
    _cli_box(
        [
            "PORSCHE STATUS SNAPSHOT",
            "",
            _cli_status_line("Kontext", f"{eingabe['kontext']} / {eingabe['wetter']} / {eingabe['uhrzeit']}"),
            _cli_status_line("Fahrerzustand", fahrerzustand_anzeige),
            _cli_status_line("Risiko-Score", f"{risiko_score:03d}/100"),
            _cli_status_line("Warnstufe", f"{warnmarker}  {_format_warning_stage(str(bewertung['warnstufe']))}"),
            _cli_status_line("Assistenzmodus", assistenzmodus_anzeige),
            _cli_status_line("Lichtmodus", bewertung["lichtmodus"]),
            _cli_status_line("Empfehlung", bewertung["empfehlung"]),
        ],
        width=92,
    )
    print()
    _cli_box(
        [
            "Systembericht abgeschlossen. Fahrzeuglogik verbleibt im Bereitschaftsmodus.",
            "Ein neuer Analysezyklus kann direkt gestartet werden.",
        ],
        width=72,
    )


def show_demo_header(name: str, beschreibung: str) -> None:
    show_section("Referenzfahrt")
    _cli_field("Szenarioprofil", name)
    _cli_field("Diagnosekontext", beschreibung)
    print()
    _cli_box(["Referenzfahrt geladen. Cockpit-Diagnose wird initialisiert."], width=64)


def show_goodbye() -> None:
    print()
    _cli_box(["Sitzung beendet. Porsche Driver State Analyzer offline."], width=66)


def starte_ui(anzeige: dict[str, str]) -> None:
    fenster = tk.Tk()
    fenster.title(anzeige.get("titel", "Ambient-Assistenzsystem"))
    fenster.geometry("1380x960")
    fenster.minsize(1240, 860)
    fenster.configure(bg=PALETTE["bg"])
    fenster.lift()
    fenster.attributes("-topmost", True)
    fenster.after(300, lambda: fenster.attributes("-topmost", False))
    fenster.focus_force()

    style = ttk.Style()
    style.theme_use("clam")
    konfiguriere_stile(style)

    matplotlib_verfuegbar = ist_matplotlib_verfuegbar()

    uhrzeit_var = tk.StringVar(value=anzeige.get("uhrzeit", "09:30"))
    stresslevel_var = tk.IntVar(value=25)
    energielevel_var = tk.IntVar(value=80)
    fokuslevel_var = tk.IntVar(value=70)
    driving_context_var = tk.StringVar(value=anzeige.get("driving_context", DRIVING_CONTEXTS[0]))
    weather_var = tk.StringVar(value=anzeige.get("weather", WEATHER_CONDITIONS[0]))

    aussenrahmen = tk.Frame(fenster, bg=PALETTE["bg"], padx=20, pady=20)
    aussenrahmen.pack(fill="both", expand=True)

    hauptpanel = tk.Frame(
        aussenrahmen,
        bg=PALETTE["bg_secondary"],
        highlightbackground=PALETTE["panel_border"],
        highlightthickness=1,
        bd=0,
    )
    hauptpanel.pack(fill="both", expand=True)

    erstelle_header(hauptpanel, anzeige.get("titel", "Ambient-Assistenzsystem"))

    content_frame = tk.Frame(hauptpanel, bg=PALETTE["bg_secondary"], padx=18, pady=18)
    content_frame.pack(fill="both", expand=True)
    content_frame.grid_columnconfigure(0, weight=3)
    content_frame.grid_columnconfigure(1, weight=7)
    content_frame.grid_columnconfigure(2, weight=5)
    content_frame.grid_rowconfigure(0, weight=1)

    sidebar_spalte = tk.Frame(content_frame, bg=PALETTE["bg_secondary"])
    sidebar_spalte.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

    mitte_spalte = tk.Frame(content_frame, bg=PALETTE["bg_secondary"])
    mitte_spalte.grid(row=0, column=1, sticky="nsew", padx=(0, 12))

    rechte_spalte = tk.Frame(content_frame, bg=PALETTE["bg_secondary"])
    rechte_spalte.grid(row=0, column=2, sticky="nsew")

    sidebar_rail = panel_frame(sidebar_spalte, variant="accent", accent=PALETTE["cyan"], dense=True)
    sidebar_rail.pack(fill="x", pady=(0, 12))

    panel_heading(
        sidebar_rail,
        "NAV / STATUS RAIL",
        "Feste Systemschiene wie in einem instrumentierten Cockpit.",
        PALETTE["cyan"],
    )

    rail_sys = rail_block(sidebar_rail.inner, "SYS", "SYNC ACTIVE", PALETTE["cyan"])
    rail_data = rail_block(sidebar_rail.inner, "DAT", "DATA STREAM ONLINE", PALETTE["cyan"])
    rail_drv = rail_block(sidebar_rail.inner, "DRV", anzeige.get("mentaler_zustand", "-"), PALETTE["amber"])
    rail_mode = rail_block(sidebar_rail.inner, "MOD", anzeige.get("modus", "-"), PALETTE["violet"])
    rail_ctx = rail_block(sidebar_rail.inner, "CTX", anzeige.get("driving_context", "-"), PALETTE["lime"])

    sidebar_panel = panel_frame(sidebar_spalte, variant="accent", accent=PALETTE["amber"], dense=True)
    sidebar_panel.pack(fill="x", pady=(0, 12))

    panel_heading(
        sidebar_panel,
        "SYSTEM STATUS",
        "Vertikale Cockpit-Sidebar fuer Kontext, Zustand und Live-Metriken.",
        PALETTE["amber"],
    )

    sidebar_mode = zeige_zeile(sidebar_panel.inner, "Driving Mode", anzeige.get("modus", "-"))
    sidebar_state = zeige_zeile(sidebar_panel.inner, "Driver State", anzeige.get("mentaler_zustand", "-"))
    sidebar_coffee = zeige_zeile(sidebar_panel.inner, "Coffee", anzeige.get("coffee_recommendation", "-"))
    sidebar_recommendation = zeige_zeile(
        sidebar_panel.inner,
        "Assist Recommendation",
        anzeige.get("empfehlung", "-"),
        umbruch=220,
    )

    sidebar_stats = panel_card(sidebar_panel.inner)
    sidebar_stats.pack(fill="x", pady=(6, 0))
    tk.Label(
        sidebar_stats,
        text="LIVE METRICS",
        font=("Consolas", 10, "bold"),
        bg=sidebar_stats.cget("bg"),
        fg=PALETTE["cyan"],
        anchor="w",
    ).pack(fill="x")
    tk.Frame(sidebar_stats, bg=PALETTE["grid"], height=1).pack(fill="x", pady=(8, 8))
    sidebar_time_value = status_readout(sidebar_stats, "TIME")
    sidebar_context_value = status_readout(sidebar_stats, "CONTEXT")
    sidebar_stress_value = status_readout(sidebar_stats, "STRESS")
    sidebar_energy_value = status_readout(sidebar_stats, "ENERGY")
    sidebar_focus_value = status_readout(sidebar_stats, "FOCUS")

    sidebar_compact = panel_card(sidebar_panel.inner)
    sidebar_compact.pack(fill="x", pady=(8, 0))
    tk.Label(
        sidebar_compact,
        text="SYSTEM STATUS / COMPACT",
        font=("Consolas", 10, "bold"),
        bg=sidebar_compact.cget("bg"),
        fg=PALETTE["amber"],
        anchor="w",
    ).pack(fill="x")
    tk.Frame(sidebar_compact, bg=PALETTE["grid"], height=1).pack(fill="x", pady=(8, 8))
    sidebar_color_value = status_readout(sidebar_compact, "AMBIENT")
    sidebar_sync_value = status_readout(sidebar_compact, "SYNC")
    sidebar_feed_value = status_readout(sidebar_compact, "FEED")

    hud_banner = panel_frame(mitte_spalte, variant="accent", accent=PALETTE["cyan"], dense=True)
    hud_banner.pack(fill="x", pady=(0, 12))

    panel_heading(
        hud_banner,
        "PRIMARY HUD",
        "Breites Fahrzeug-HUD fuer Driver State, Driving Mode und aktiven Fahrkontext.",
        PALETTE["cyan"],
    )

    banner_grid = tk.Frame(hud_banner.inner, bg=hud_banner.inner.cget("bg"))
    banner_grid.pack(fill="x")
    for spalte in range(4):
        banner_grid.grid_columnconfigure(spalte, weight=1)

    banner_state = banner_metric(banner_grid, "DRIVER STATE", anzeige.get("mentaler_zustand", "-"), 0, 0, PALETTE["cyan"])
    banner_mode = banner_metric(banner_grid, "DRIVING MODE", anzeige.get("modus", "-"), 0, 1, PALETTE["amber"])
    banner_context = banner_metric(banner_grid, "CONTEXT", anzeige.get("driving_context", "-"), 0, 2, PALETTE["violet"])
    banner_time = banner_metric(banner_grid, "SYSTEM TIME", anzeige.get("uhrzeit", "-"), 0, 3, PALETTE["lime"])

    hud_strip = panel_card(hud_banner.inner)
    hud_strip.pack(fill="x", pady=(8, 0))
    tk.Label(
        hud_strip,
        text="HUD FEED",
        font=("Consolas", 10, "bold"),
        bg=hud_strip.cget("bg"),
        fg=PALETTE["cyan"],
        anchor="w",
    ).pack(fill="x")
    tk.Frame(hud_strip, bg=PALETTE["grid"], height=1).pack(fill="x", pady=(8, 8))
    hud_recommendation = status_readout(hud_strip, "ACTION")
    hud_coffee = status_readout(hud_strip, "COFFEE")
    hud_ambient = status_readout(hud_strip, "AMBIENT")

    warning_panel = panel_card(hud_banner.inner)
    warning_panel.pack(fill="x", pady=(8, 0))
    warning_top = tk.Frame(warning_panel, bg=warning_panel.cget("bg"))
    warning_top.pack(fill="x")
    tk.Label(
        warning_top,
        text="WARNING SYSTEM",
        font=("Consolas", 10, "bold"),
        bg=warning_panel.cget("bg"),
        fg=PALETTE["danger"],
        anchor="w",
    ).pack(side="left")
    tk.Label(
        warning_top,
        text="LIVE",
        font=("Consolas", 9, "bold"),
        bg=warning_panel.cget("bg"),
        fg=PALETTE["muted"],
        anchor="e",
    ).pack(side="right")
    tk.Frame(warning_panel, bg=PALETTE["grid"], height=1).pack(fill="x", pady=(8, 8))
    warning_label = tk.Label(
        warning_panel,
        text="SYSTEM STABLE",
        font=("Bahnschrift SemiBold", 14),
        bg=warning_panel.cget("bg"),
        fg=PALETTE["cyan"],
        anchor="w",
        justify="left",
        wraplength=640,
    )
    warning_label.pack(fill="x")

    steuerung_panel = panel_frame(mitte_spalte, variant="standard")
    steuerung_panel.pack(fill="x", pady=(0, 12))

    panel_heading(
        steuerung_panel,
        "INPUT / TELEMETRY MATRIX",
        "Cockpit-Parameter in einer haerteren Survival-HUD-Struktur.",
        PALETTE["cyan"],
    )

    fehler_label = tk.Label(
        steuerung_panel.inner,
        text="",
        font=("Bahnschrift SemiBold", 10),
        bg=steuerung_panel.inner.cget("bg"),
        fg=PALETTE["danger"],
        anchor="w",
    )
    fehler_label.pack(fill="x", pady=(0, 10))

    matrix_grid = tk.Frame(steuerung_panel.inner, bg=steuerung_panel.inner.cget("bg"))
    matrix_grid.pack(fill="both", expand=True)

    matrix_top = tk.Frame(matrix_grid, bg=matrix_grid.cget("bg"))
    matrix_top.pack(fill="x", pady=(0, 8))

    time_frame = panel_card(matrix_top)
    time_frame.pack(side="left", fill="x", expand=True, padx=(0, 6))
    tk.Label(
        time_frame,
        text="TIME VECTOR",
        font=("Consolas", 10, "bold"),
        bg=time_frame.cget("bg"),
        fg=PALETTE["cyan"],
        anchor="w",
    ).pack(fill="x")
    tk.Label(
        time_frame,
        text="24H SYSTEM CLOCK",
        font=("Consolas", 9, "bold"),
        bg=time_frame.cget("bg"),
        fg=PALETTE["muted"],
        anchor="w",
    ).pack(fill="x", pady=(4, 8))
    time_entry = tk.Entry(
        time_frame,
        textvariable=uhrzeit_var,
        font=("Bahnschrift", 12),
        bg=PALETTE["entry_bg"],
        fg=PALETTE["text"],
        insertbackground=PALETTE["text"],
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=PALETTE["panel_border"],
        highlightcolor=PALETTE["cyan"],
    )
    time_entry.pack(fill="x", ipady=8)

    context_frame = panel_card(matrix_top)
    context_frame.pack(side="left", fill="x", expand=True, padx=(6, 0))
    tk.Label(
        context_frame,
        text="DRIVING CONTEXT",
        font=("Consolas", 10, "bold"),
        bg=context_frame.cget("bg"),
        fg=PALETTE["violet"],
        anchor="w",
    ).pack(fill="x")
    tk.Label(
        context_frame,
        text="ACTIVE SCENARIO",
        font=("Consolas", 9, "bold"),
        bg=context_frame.cget("bg"),
        fg=PALETTE["muted"],
        anchor="w",
    ).pack(fill="x", pady=(4, 8))
    driving_context_combo = ttk.Combobox(
        context_frame,
        textvariable=driving_context_var,
        values=DRIVING_CONTEXTS,
        state="readonly",
        font=("Bahnschrift", 12),
        style="Cyber.TCombobox",
    )
    driving_context_combo.pack(fill="x", ipady=2)

    weather_frame = panel_card(matrix_top)
    weather_frame.pack(side="left", fill="x", expand=True, padx=(6, 0))
    tk.Label(
        weather_frame,
        text="WEATHER",
        font=("Consolas", 10, "bold"),
        bg=weather_frame.cget("bg"),
        fg=PALETTE["lime"],
        anchor="w",
    ).pack(fill="x")
    tk.Label(
        weather_frame,
        text="ROAD CONDITIONS",
        font=("Consolas", 9, "bold"),
        bg=weather_frame.cget("bg"),
        fg=PALETTE["muted"],
        anchor="w",
    ).pack(fill="x", pady=(4, 8))
    weather_combo = ttk.Combobox(
        weather_frame,
        textvariable=weather_var,
        values=WEATHER_CONDITIONS,
        state="readonly",
        font=("Bahnschrift", 12),
        style="Cyber.TCombobox",
    )
    weather_combo.pack(fill="x", ipady=2)

    telemetry_tiles = tk.Frame(
        matrix_grid,
        bg=steuerung_panel.inner.cget("bg"),
    )
    telemetry_tiles.pack(fill="x", pady=(2, 0))

    stress_tile = baue_telemetriekachel_pack(
        telemetry_tiles, "STRESS LEVEL", stresslevel_var, PALETTE["danger"]
    )
    energy_tile = baue_telemetriekachel_pack(
        telemetry_tiles, "ENERGY LEVEL", energielevel_var, PALETTE["amber"]
    )
    focus_tile = baue_telemetriekachel_pack(
        telemetry_tiles, "FOCUS LEVEL", fokuslevel_var, PALETTE["cyan"]
    )

    ambient_panel = panel_frame(mitte_spalte, variant="accent", accent=PALETTE["cyan"], dense=True)
    ambient_panel.pack(fill="x", pady=(0, 12))

    aktuelle_farbe = anzeige.get("farbe_hex", "#3498DB")
    animation_job: str | None = None

    ambient_zone = tk.Frame(
        ambient_panel.inner,
        bg=aktuelle_farbe,
        padx=24,
        pady=22,
        highlightbackground=PALETTE["panel_glow"],
        highlightthickness=1,
        bd=0,
    )
    ambient_zone.pack(fill="x")

    ambient_topbar = tk.Frame(ambient_zone, bg=aktuelle_farbe)
    ambient_topbar.pack(fill="x")

    ambient_kicker = tk.Label(
        ambient_topbar,
        text="AMBIENT ZONE / PRIMARY FEEDBACK",
        font=("Bahnschrift SemiBold", 11),
        bg=aktuelle_farbe,
        fg=ermittle_textfarbe(aktuelle_farbe),
        anchor="w",
    )
    ambient_kicker.pack(side="left")

    ambient_badge = tk.Label(
        ambient_topbar,
        text="STABLE",
        font=("Consolas", 10, "bold"),
        bg=aktuelle_farbe,
        fg=ermittle_textfarbe(aktuelle_farbe),
        padx=10,
        pady=4,
        highlightbackground=ermittle_textfarbe(aktuelle_farbe),
        highlightthickness=1,
    )
    ambient_badge.pack(side="right")

    ambient_titel = tk.Label(
        ambient_zone,
        text=anzeige.get("titel", "Ambient Assistance System"),
        font=("Bahnschrift SemiBold", 26),
        bg=aktuelle_farbe,
        fg=ermittle_textfarbe(aktuelle_farbe),
        anchor="w",
    )
    ambient_titel.pack(fill="x", pady=(16, 8))

    ambient_state_row = tk.Frame(ambient_zone, bg=aktuelle_farbe)
    ambient_state_row.pack(fill="x", pady=(0, 12))

    ambient_zustand = tk.Label(
        ambient_state_row,
        text=f"Driver State: {anzeige.get('mentaler_zustand', '-')}",
        font=("Bahnschrift", 16),
        bg=aktuelle_farbe,
        fg=ermittle_textfarbe(aktuelle_farbe),
        anchor="w",
    )
    ambient_zustand.pack(side="left")

    ambient_farbe = tk.Label(
        ambient_state_row,
        text=f"{anzeige.get('farbname', 'Neutral')}  {aktuelle_farbe}",
        font=("Consolas", 12, "bold"),
        bg=aktuelle_farbe,
        fg=ermittle_textfarbe(aktuelle_farbe),
        anchor="e",
    )
    ambient_farbe.pack(side="right")

    ambient_hinweis = tk.Label(
        ambient_zone,
        text="Dominantes Feedback-Feld fuer mentale Last, Wachheit und Fahrmodus. Die Zone ist absichtlich wie ein HMI-Hauptmonitor gewichtet.",
        font=("Bahnschrift", 11),
        bg=aktuelle_farbe,
        fg=ermittle_textfarbe(aktuelle_farbe),
        anchor="w",
        justify="left",
        wraplength=650,
    )
    ambient_hinweis.pack(fill="x")

    status_panel = panel_frame(mitte_spalte, variant="standard")
    status_panel.pack(fill="x", pady=(0, 12))

    panel_heading(
        status_panel,
        "SYSTEM OVERVIEW",
        "Live-Telemetrie als modulare Cockpit-Kacheln mit staerkerem HUD-Kontrast.",
        PALETTE["amber"],
    )

    kachel_rahmen = tk.Frame(status_panel.inner, bg=status_panel.inner.cget("bg"))
    kachel_rahmen.pack(fill="x")

    for spalte in range(3):
        kachel_rahmen.grid_columnconfigure(spalte, weight=1)

    uhrzeit_kachel = erstelle_statuskachel(kachel_rahmen, "Time", 0, 0)
    fahrkontext_kachel = erstelle_statuskachel(kachel_rahmen, "Driving Context", 0, 1)
    fahrerzustand_kachel = erstelle_statuskachel(kachel_rahmen, "Driver State", 0, 2)
    stress_kachel = erstelle_statuskachel(kachel_rahmen, "Stress Level", 1, 0)
    energie_kachel = erstelle_statuskachel(kachel_rahmen, "Energy Level", 1, 1)
    fokus_kachel = erstelle_statuskachel(kachel_rahmen, "Focus Level", 1, 2)

    aktion_panel = panel_frame(rechte_spalte, variant="accent", accent=PALETTE["violet"])
    aktion_panel.pack(fill="x", pady=(0, 12))

    panel_heading(
        aktion_panel,
        "TACTICAL TOOLS",
        "Externe Visualisierung und Analysefunktionen in einem separaten Command-Panel.",
        PALETTE["violet"],
    )

    visualisieren_button = tk.Button(
        aktion_panel.inner,
        text="INITIATE 3D STATE SCAN",
        font=("Bahnschrift SemiBold", 12),
        bg=PALETTE["cyan"],
        fg=PALETTE["bg"],
        activebackground="#7FEBFF",
        activeforeground=PALETTE["bg"],
        disabledforeground="#D5DFEA",
        cursor="hand2",
        padx=16,
        pady=12,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=PALETTE["panel_glow"],
        command=lambda: visualisiere_zustand(
            stresslevel_var.get(),
            energielevel_var.get(),
            fokuslevel_var.get(),
        ),
    )
    visualisieren_button.pack(fill="x")

    tool_status = tk.Label(
        aktion_panel.inner,
        text="READY / EXTERNAL VISUALIZATION LINK",
        font=("Consolas", 10, "bold"),
        bg=aktion_panel.inner.cget("bg"),
        fg=PALETTE["amber"],
        anchor="w",
    )
    tool_status.pack(fill="x", pady=(10, 0))

    diag_strip = panel_card(aktion_panel.inner)
    diag_strip.pack(fill="x", pady=(10, 0))
    diag_top = tk.Frame(diag_strip, bg=diag_strip.cget("bg"))
    diag_top.pack(fill="x")
    tk.Label(
        diag_top,
        text="DIAGNOSTICS",
        font=("Consolas", 10, "bold"),
        bg=diag_strip.cget("bg"),
        fg=PALETTE["violet"],
    ).pack(side="left")
    tk.Label(
        diag_top,
        text="COMPACT",
        font=("Consolas", 9, "bold"),
        bg=diag_strip.cget("bg"),
        fg=PALETTE["muted"],
    ).pack(side="right")
    tk.Frame(diag_strip, bg=PALETTE["grid"], height=1).pack(fill="x", pady=(8, 8))
    diag_time = status_readout(diag_strip, "TIME")
    diag_context = status_readout(diag_strip, "CONTEXT")
    diag_mode = status_readout(diag_strip, "MODE")

    if not matplotlib_verfuegbar:
        visualisieren_button.config(state="disabled", bg="#486277", highlightbackground="#486277")
        tool_status.config(text="OFFLINE / MATPLOTLIB REQUIRED", fg=PALETTE["danger"])
        tk.Label(
            aktion_panel.inner,
            text="Matplotlib nicht installiert. Fuer die 3D-Ansicht: pip install matplotlib",
            font=("Bahnschrift", 10),
            bg=aktion_panel.inner.cget("bg"),
            fg=PALETTE["muted"],
            anchor="w",
            justify="left",
            wraplength=320,
        ).pack(fill="x", pady=(8, 0))

    details_panel = panel_frame(rechte_spalte, variant="standard")
    details_panel.pack(fill="both", expand=True)

    panel_heading(
        details_panel,
        "ASSISTANCE INTELLIGENCE",
        "Operator-Ansicht mit Input, Interpretation und Action auf Basis der aktiven Systemwerte.",
        PALETTE["cyan"],
    )

    intelligence_input = intelligence_section(details_panel.inner, "INPUT", PALETTE["cyan"])
    input_time_value = status_readout(intelligence_input, "TIME VECTOR")
    input_context_value = status_readout(intelligence_input, "ACTIVE CONTEXT")
    input_weather_value = status_readout(intelligence_input, "WEATHER")
    input_stress_value = status_readout(intelligence_input, "STRESS")
    input_energy_value = status_readout(intelligence_input, "ENERGY")
    input_focus_value = status_readout(intelligence_input, "FOCUS")

    intelligence_interpretation = intelligence_section(details_panel.inner, "INTERPRETATION", PALETTE["amber"])
    kontext_wert = status_readout(intelligence_interpretation, "SCENARIO")
    wetter_wert = status_readout(intelligence_interpretation, "WEATHER")
    modus_wert = status_readout(intelligence_interpretation, "DRIVING MODE")
    zustand_wert = status_readout(intelligence_interpretation, "DRIVER STATE")
    begruendung_wert = intelligence_text_block(
        intelligence_interpretation,
        "RATIONALE",
        anzeige.get("begruendung", "-"),
    )

    intelligence_action = intelligence_section(details_panel.inner, "ACTION", PALETTE["violet"])
    empfehlung_wert = intelligence_text_block(
        intelligence_action,
        "SYSTEM RECOMMENDATION",
        anzeige.get("empfehlung", "-"),
    )
    kaffee_wert = status_readout(intelligence_action, "COFFEE")
    kaffee_grund_wert = intelligence_text_block(
        intelligence_action,
        "COFFEE RATIONALE",
        anzeige.get("coffee_reason", "-"),
    )

    # Die Ambient-Zone bleibt das dominante HUD-Element und erhaelt bei jedem Zustandswechsel Badge und Rahmenfarbe synchron.
    def setze_ambient_farbe(farbe_hex: str, zustand: str) -> None:
        ui_farben = ermittle_ui_farben(zustand, farbe_hex)
        textfarbe = ermittle_textfarbe(farbe_hex)
        ambient_panel.config(highlightbackground=ui_farben["accent"])
        ambient_zone.config(bg=farbe_hex, highlightbackground=ui_farben["accent"])
        ambient_topbar.config(bg=farbe_hex)
        ambient_state_row.config(bg=farbe_hex)
        ambient_kicker.config(bg=farbe_hex, fg=textfarbe)
        ambient_badge.config(
            bg=ui_farben["surface"],
            fg=ui_farben["accent"],
            text=ui_farben["badge"],
            highlightbackground=ui_farben["accent"],
        )
        ambient_titel.config(bg=farbe_hex, fg=textfarbe)
        ambient_zustand.config(bg=farbe_hex, fg=textfarbe)
        ambient_farbe.config(bg=farbe_hex, fg=textfarbe)
        ambient_hinweis.config(bg=farbe_hex, fg=textfarbe)

    def animiere_farbwechsel(
        start_hex: str,
        ziel_hex: str,
        zustand: str,
        schritt: int = 0,
        schritte: int = 16,
    ) -> None:
        nonlocal aktuelle_farbe, animation_job

        if schritt > schritte:
            aktuelle_farbe = ziel_hex
            animation_job = None
            setze_ambient_farbe(ziel_hex, zustand)
            return

        zwischenfarbe = mische_farbe(start_hex, ziel_hex, schritt / schritte)
        aktuelle_farbe = zwischenfarbe
        setze_ambient_farbe(zwischenfarbe, zustand)
        animation_job = fenster.after(
            28,
            lambda: animiere_farbwechsel(start_hex, ziel_hex, zustand, schritt + 1, schritte),
        )

    def starte_farbwechsel(ziel_hex: str, zustand: str) -> None:
        nonlocal animation_job

        if animation_job is not None:
            fenster.after_cancel(animation_job)

        if aktuelle_farbe.lower() == ziel_hex.lower():
            setze_ambient_farbe(ziel_hex, zustand)
            return

        animiere_farbwechsel(aktuelle_farbe, ziel_hex, zustand)

    def aktualisiere_statuskachel(label: tk.Label, wert: str, accent: str | None = None) -> None:
        label.config(text=wert)
        if accent:
            label.config(fg=accent)

    def synchronisiere_telemetrie() -> None:
        werte = calculate_telemetry(uhrzeit_var.get(), driving_context_var.get(), weather_var.get())
        stresslevel_var.set(werte["stresslevel"])
        energielevel_var.set(werte["energielevel"])
        fokuslevel_var.set(werte["fokuslevel"])

    def aktualisiere_telemetrie() -> None:
        aktualisiere_bar(stress_tile, stresslevel_var.get())
        aktualisiere_bar(energy_tile, energielevel_var.get())
        aktualisiere_bar(focus_tile, fokuslevel_var.get())

    def auswertung_aktualisieren(*_args: object) -> None:
        try:
            synchronisiere_telemetrie()
            auswertung = evaluate_context(
                uhrzeit_var.get(),
                stresslevel_var.get(),
                energielevel_var.get(),
                fokuslevel_var.get(),
                driving_context_var.get(),
                weather_var.get(),
            )
        except ValueError as fehler:
            fehler_label.config(text=str(fehler))
            return

        farbe = get_visual_state(auswertung["mentaler_zustand"])
        ui_farben = ermittle_ui_farben(auswertung["mentaler_zustand"], farbe["hex"])

        fehler_label.config(text="")
        starte_farbwechsel(farbe["hex"], auswertung["mentaler_zustand"])
        ambient_zustand.config(text=f"Driver State: {auswertung['mentaler_zustand']}")
        ambient_farbe.config(text=f"{farbe['farbname']}  {farbe['hex']}")
        aktualisiere_telemetrie()

        aktualisiere_statuskachel(uhrzeit_kachel, uhrzeit_var.get(), PALETTE["text"])
        aktualisiere_statuskachel(fahrkontext_kachel, driving_context_var.get(), PALETTE["text"])
        aktualisiere_statuskachel(fahrerzustand_kachel, auswertung["mentaler_zustand"], ui_farben["accent"])
        aktualisiere_statuskachel(stress_kachel, f"{stresslevel_var.get()} / 100", PALETTE["danger"])
        aktualisiere_statuskachel(energie_kachel, f"{energielevel_var.get()} / 100", PALETTE["amber"])
        aktualisiere_statuskachel(fokus_kachel, f"{fokuslevel_var.get()} / 100", PALETTE["cyan"])

        input_time_value.config(text=uhrzeit_var.get())
        input_context_value.config(text=driving_context_var.get())
        input_weather_value.config(text=weather_var.get())
        input_stress_value.config(text=f"{stresslevel_var.get():03d} / 100", fg=PALETTE["danger"])
        input_energy_value.config(text=f"{energielevel_var.get():03d} / 100", fg=PALETTE["amber"])
        input_focus_value.config(text=f"{fokuslevel_var.get():03d} / 100", fg=PALETTE["cyan"])
        kontext_wert.config(text=driving_context_var.get())
        wetter_wert.config(text=weather_var.get())
        modus_wert.config(text=auswertung["modus"], fg=ui_farben["accent"])
        zustand_wert.config(text=auswertung["mentaler_zustand"], fg=ui_farben["accent"])
        empfehlung_wert.config(text=auswertung["empfehlung"])
        begruendung_wert.config(text=auswertung["begruendung"])
        kaffee_wert.config(text=auswertung["coffee_recommendation"], fg=ui_farben["accent"])
        kaffee_grund_wert.config(text=auswertung["coffee_reason"])
        sidebar_mode.config(text=auswertung["modus"], fg=ui_farben["accent"])
        sidebar_state.config(text=auswertung["mentaler_zustand"], fg=ui_farben["accent"])
        sidebar_coffee.config(text=auswertung["coffee_recommendation"], fg=ui_farben["accent"])
        sidebar_recommendation.config(text=auswertung["empfehlung"])
        banner_mode.config(text=auswertung["modus"], fg=PALETTE["amber"])
        banner_state.config(text=auswertung["mentaler_zustand"], fg=ui_farben["accent"])
        banner_context.config(text=driving_context_var.get(), fg=PALETTE["violet"])
        banner_time.config(text=uhrzeit_var.get(), fg=PALETTE["lime"])
        hud_recommendation.config(text=auswertung["empfehlung"], fg=PALETTE["text"])
        hud_coffee.config(text=auswertung["coffee_recommendation"], fg=ui_farben["accent"])
        hud_ambient.config(text=f"{farbe['farbname']} / {farbe['hex']}", fg=ui_farben["accent"])

        warnungen: list[str] = []
        warnfarbe = PALETTE["cyan"]
        if stresslevel_var.get() > 80:
            warnungen.append("HIGH LOAD DETECTED")
            warnfarbe = PALETTE["danger"]
        if energielevel_var.get() < 30:
            warnungen.append("FATIGUE RISK")
            if warnfarbe != PALETTE["danger"]:
                warnfarbe = PALETTE["amber"]
        if warnungen:
            warning_label.config(text="  |  ".join(warnungen), fg=warnfarbe)
        else:
            warning_label.config(text="SYSTEM STABLE", fg=PALETTE["cyan"])

        sidebar_time_value.config(text=uhrzeit_var.get())
        sidebar_context_value.config(text=driving_context_var.get())
        sidebar_stress_value.config(text=f"{stresslevel_var.get():03d}")
        sidebar_energy_value.config(text=f"{energielevel_var.get():03d}")
        sidebar_focus_value.config(text=f"{fokuslevel_var.get():03d}")
        sidebar_color_value.config(text=f"{farbe['farbname']} / {farbe['hex']}", fg=ui_farben["accent"])
        sidebar_sync_value.config(text="ACTIVE", fg=PALETTE["cyan"])
        sidebar_feed_value.config(text="ONLINE", fg=PALETTE["cyan"])
        rail_sys.config(text="SYNC ACTIVE", fg=PALETTE["cyan"])
        rail_data.config(text="DATA STREAM ONLINE", fg=PALETTE["cyan"])
        rail_drv.config(text=auswertung["mentaler_zustand"], fg=ui_farben["accent"])
        rail_mode.config(text=auswertung["modus"], fg=ui_farben["accent"])
        rail_ctx.config(text=driving_context_var.get(), fg=PALETTE["lime"])
        diag_time.config(text=uhrzeit_var.get())
        diag_context.config(text=driving_context_var.get())
        diag_mode.config(text=auswertung["modus"])

    uhrzeit_var.trace_add("write", auswertung_aktualisieren)
    driving_context_var.trace_add("write", auswertung_aktualisieren)
    weather_var.trace_add("write", auswertung_aktualisieren)

    auswertung_aktualisieren()

    fenster.mainloop()


def konfiguriere_stile(style: ttk.Style) -> None:
    style.configure(
        "Cyber.TCombobox",
        fieldbackground=PALETTE["entry_bg"],
        background=PALETTE["entry_bg"],
        foreground=PALETTE["text"],
        bordercolor=PALETTE["panel_border"],
        lightcolor=PALETTE["panel_border"],
        darkcolor=PALETTE["panel_border"],
        arrowcolor=PALETTE["cyan"],
        relief="flat",
        padding=(10, 8),
        insertcolor=PALETTE["text"],
    )
    style.map(
        "Cyber.TCombobox",
        fieldbackground=[("readonly", PALETTE["entry_bg"])],
        background=[("readonly", PALETTE["entry_bg"])],
        foreground=[("readonly", PALETTE["text"])],
        bordercolor=[("focus", PALETTE["cyan"]), ("readonly", PALETTE["panel_border"])],
        arrowcolor=[("focus", PALETTE["amber"]), ("readonly", PALETTE["cyan"])],
    )

def erstelle_header(elternteil: tk.Widget, titel: str) -> None:
    header = tk.Frame(
        elternteil,
        bg=PALETTE["bg_secondary"],
        highlightbackground=PALETTE["panel_border"],
        highlightthickness=1,
        padx=18,
        pady=14,
    )
    header.pack(fill="x", padx=18, pady=(18, 0))

    left = tk.Frame(header, bg=PALETTE["bg_secondary"])
    left.pack(side="left", fill="x", expand=True)

    badge_row = tk.Frame(left, bg=PALETTE["bg_secondary"])
    badge_row.pack(fill="x")

    for text, color in [
        ("COCKPIT ASSIST", PALETTE["cyan"]),
        ("SURVIVAL HUD", PALETTE["amber"]),
        ("VEHICLE AI", PALETTE["violet"]),
    ]:
        tk.Label(
            badge_row,
            text=text,
            font=("Consolas", 10, "bold"),
            bg=PALETTE["panel"],
            fg=color,
            padx=10,
            pady=4,
            highlightbackground=color,
            highlightthickness=1,
        ).pack(side="left", padx=(0, 8))

    tk.Label(
        left,
        text=titel,
        font=("Bahnschrift SemiBold", 28),
        bg=PALETTE["bg_secondary"],
        fg=PALETTE["text"],
        anchor="w",
    ).pack(fill="x", pady=(12, 0))

    tk.Label(
        left,
        text="Dunkles Sci-Fi-Cockpit mit taktischen Panels, Neon-Akzenten und klarer HMI-Gewichtung.",
        font=("Bahnschrift", 11),
        bg=PALETTE["bg_secondary"],
        fg=PALETTE["muted"],
        anchor="w",
    ).pack(fill="x", pady=(4, 0))

    right = tk.Frame(
        header,
        bg=PALETTE["panel_deep"],
        highlightbackground=PALETTE["panel_glow"],
        highlightthickness=1,
        padx=14,
        pady=10,
    )
    right.pack(side="right")

    tk.Label(
        right,
        text="STATUS",
        font=("Consolas", 10, "bold"),
        bg=PALETTE["panel_deep"],
        fg=PALETTE["amber"],
    ).pack(anchor="e")

    tk.Label(
        right,
        text="ONLINE",
        font=("Bahnschrift SemiBold", 18),
        bg=PALETTE["panel_deep"],
        fg=PALETTE["text"],
    ).pack(anchor="e")


def panel_frame(
    elternteil: tk.Widget,
    variant: str = "standard",
    accent: str | None = None,
    dense: bool = False,
) -> tk.Frame:
    accent_color = accent or PALETTE["panel_border"]
    outer = tk.Frame(
        elternteil,
        bg=PALETTE["bg_secondary"],
        highlightbackground=accent_color if variant == "accent" else PALETTE["panel_border"],
        highlightthickness=1,
        bd=0,
        padx=1,
        pady=1,
    )

    shell_bg = PALETTE["panel_deep"] if variant == "accent" else PALETTE["panel"]
    shell = tk.Frame(outer, bg=shell_bg, bd=0)
    shell.pack(fill="both", expand=True)

    top_line = tk.Frame(shell, bg=accent_color if variant == "accent" else PALETTE["grid"], height=2)
    top_line.pack(fill="x")

    inner = tk.Frame(shell, bg=shell_bg, padx=14 if dense else 16, pady=12 if dense else 16)
    inner.pack(fill="both", expand=True)

    grid_strip = tk.Canvas(
        inner,
        height=14,
        bg=shell_bg,
        highlightthickness=0,
        bd=0,
    )
    grid_strip.pack(fill="x", pady=(0, 12))
    grid_strip.bind("<Configure>", lambda event, target=grid_strip: zeichne_gridstrip(target))

    outer.inner = inner
    return outer


def panel_card(elternteil: tk.Widget) -> tk.Frame:
    karte = tk.Frame(
        elternteil,
        bg=PALETTE["panel_alt"],
        highlightbackground=PALETTE["panel_border"],
        highlightthickness=1,
        bd=0,
        padx=12,
        pady=10,
    )
    karte.bind("<Configure>", lambda event, target=karte: zeichne_panel_ecken(target))
    return karte


def panel_heading(elternteil: tk.Widget, titel: str, untertitel: str, accent: str) -> None:
    kopf = tk.Frame(elternteil.inner, bg=elternteil.inner.cget("bg"))
    kopf.pack(fill="x", pady=(0, 14))

    top = tk.Frame(kopf, bg=elternteil.inner.cget("bg"))
    top.pack(fill="x")

    tk.Label(
        top,
        text=titel,
        font=("Bahnschrift SemiBold", 14),
        bg=elternteil.inner.cget("bg"),
        fg=accent,
        anchor="w",
    ).pack(side="left")

    tk.Label(
        top,
        text="///",
        font=("Consolas", 11, "bold"),
        bg=elternteil.inner.cget("bg"),
        fg=PALETTE["muted"],
        anchor="e",
    ).pack(side="right")

    tk.Label(
        kopf,
        text=untertitel,
        font=("Bahnschrift", 10),
        bg=elternteil.inner.cget("bg"),
        fg=PALETTE["muted"],
        anchor="w",
        justify="left",
        wraplength=720,
    ).pack(fill="x", pady=(4, 0))


def status_readout(elternteil: tk.Widget, titel: str) -> tk.Label:
    zeile = tk.Frame(elternteil, bg=elternteil.cget("bg"))
    zeile.pack(fill="x", pady=3)

    tk.Label(
        zeile,
        text=titel,
        font=("Consolas", 9, "bold"),
        bg=elternteil.cget("bg"),
        fg=PALETTE["muted"],
        anchor="w",
    ).pack(side="left")

    wert = tk.Label(
        zeile,
        text="-",
        font=("Consolas", 10, "bold"),
        bg=elternteil.cget("bg"),
        fg=PALETTE["text"],
        anchor="e",
    )
    wert.pack(side="right")

    return wert


def rail_block(elternteil: tk.Widget, code: str, wert: str, accent: str) -> tk.Label:
    block = panel_card(elternteil)
    block.pack(fill="x", pady=4)

    top = tk.Frame(block, bg=block.cget("bg"))
    top.pack(fill="x")
    tk.Label(
        top,
        text=code,
        font=("Consolas", 10, "bold"),
        bg=block.cget("bg"),
        fg=accent,
    ).pack(side="left")
    tk.Label(
        top,
        text="[]",
        font=("Consolas", 9, "bold"),
        bg=block.cget("bg"),
        fg=PALETTE["muted"],
    ).pack(side="right")

    label = tk.Label(
        block,
        text=wert,
        font=("Bahnschrift SemiBold", 11),
        bg=block.cget("bg"),
        fg=PALETTE["text"],
        anchor="w",
        justify="left",
        wraplength=180,
    )
    label.pack(fill="x", pady=(6, 0))
    return label


def banner_metric(elternteil: tk.Widget, titel: str, wert: str, zeile: int, spalte: int, accent: str) -> tk.Label:
    block = panel_card(elternteil)
    block.grid(row=zeile, column=spalte, sticky="nsew", padx=4, pady=4)

    tk.Label(
        block,
        text=titel,
        font=("Consolas", 10, "bold"),
        bg=block.cget("bg"),
        fg=accent,
        anchor="w",
    ).pack(fill="x")
    tk.Frame(block, bg=PALETTE["grid"], height=1).pack(fill="x", pady=(6, 8))

    wert_label = tk.Label(
        block,
        text=wert,
        font=("Bahnschrift SemiBold", 14),
        bg=block.cget("bg"),
        fg=PALETTE["text"],
        anchor="w",
        justify="left",
        wraplength=180,
    )
    wert_label.pack(fill="x")
    return wert_label


def intelligence_section(elternteil: tk.Widget, titel: str, accent: str) -> tk.Frame:
    section = panel_card(elternteil)
    section.pack(fill="x", pady=6)

    top = tk.Frame(section, bg=section.cget("bg"))
    top.pack(fill="x")
    tk.Label(
        top,
        text=titel,
        font=("Consolas", 11, "bold"),
        bg=section.cget("bg"),
        fg=accent,
        anchor="w",
    ).pack(side="left")
    tk.Label(
        top,
        text="[]",
        font=("Consolas", 10, "bold"),
        bg=section.cget("bg"),
        fg=PALETTE["muted"],
    ).pack(side="right")
    tk.Frame(section, bg=PALETTE["grid"], height=1).pack(fill="x", pady=(8, 8))
    return section


def intelligence_text_block(elternteil: tk.Widget, titel: str, wert: str) -> tk.Label:
    block = tk.Frame(elternteil, bg=elternteil.cget("bg"))
    block.pack(fill="x", pady=4)

    tk.Label(
        block,
        text=titel,
        font=("Consolas", 9, "bold"),
        bg=elternteil.cget("bg"),
        fg=PALETTE["muted"],
        anchor="w",
    ).pack(fill="x")

    wert_label = tk.Label(
        block,
        text=wert,
        font=("Bahnschrift", 11),
        bg=elternteil.cget("bg"),
        fg=PALETTE["text"],
        anchor="w",
        justify="left",
        wraplength=340,
    )
    wert_label.pack(fill="x", pady=(6, 0))
    return wert_label


def baue_input_kachel(
    elternteil: tk.Widget,
    titel: str,
    zusatz: str,
    accent: str,
    zeile: int,
    spalte: int,
    columnspan: int,
) -> tuple[dict[str, tk.Widget | str], tk.Widget]:
    karte = panel_card(elternteil)
    karte.grid(row=zeile, column=spalte, columnspan=columnspan, padx=5, pady=5, sticky="nsew")
    karte.grid_columnconfigure(0, weight=1)

    top = tk.Frame(karte, bg=karte.cget("bg"))
    top.pack(fill="x")
    tk.Label(
        top,
        text=titel,
        font=("Consolas", 10, "bold"),
        bg=karte.cget("bg"),
        fg=accent,
        anchor="w",
    ).pack(side="left")
    tk.Label(
        top,
        text="LIVE",
        font=("Consolas", 9, "bold"),
        bg=karte.cget("bg"),
        fg=PALETTE["muted"],
        anchor="e",
    ).pack(side="right")

    tk.Label(
        karte,
        text=zusatz,
        font=("Consolas", 9, "bold"),
        bg=karte.cget("bg"),
        fg=PALETTE["muted"],
        anchor="w",
    ).pack(fill="x", pady=(4, 0))

    value_label = tk.Label(
        karte,
        text="-",
        font=("Bahnschrift SemiBold", 20),
        bg=karte.cget("bg"),
        fg=PALETTE["text"],
        anchor="w",
    )
    value_label.pack(fill="x", pady=(8, 6))

    tk.Frame(karte, bg=PALETTE["grid"], height=1).pack(fill="x", pady=(0, 8))

    if titel == "TIME VECTOR":
        widget = tk.Entry(
            karte,
            font=("Bahnschrift", 12),
            bg=PALETTE["entry_bg"],
            fg=PALETTE["text"],
            insertbackground=PALETTE["text"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=PALETTE["panel_border"],
            highlightcolor=accent,
        )
        widget.pack(fill="x", ipady=8)
    else:
        widget = ttk.Combobox(
            karte,
            font=("Bahnschrift", 12),
            style="Cyber.TCombobox",
        )
        widget.pack(fill="x", ipady=2)

    return {"value_label": value_label}, widget


def aktualisiere_datenkachel(karte: dict[str, tk.Widget | str], wert: str) -> None:
    value_label = karte.get("value_label")
    if isinstance(value_label, tk.Label):
        value_label.config(text=wert)


def baue_telemetriekachel_pack(
    elternteil: tk.Widget,
    titel: str,
    variable: tk.IntVar,
    accent: str,
) -> dict[str, tk.Widget | tk.IntVar | str]:
    karte = panel_card(elternteil)
    karte.pack(side="left", fill="both", expand=True, padx=5, pady=5)

    top = tk.Frame(karte, bg=karte.cget("bg"))
    top.pack(fill="x")
    tk.Label(
        top,
        text=titel,
        font=("Consolas", 10, "bold"),
        bg=karte.cget("bg"),
        fg=accent,
        anchor="w",
    ).pack(side="left")
    tk.Label(
        top,
        text="LIVE",
        font=("Consolas", 9, "bold"),
        bg=karte.cget("bg"),
        fg=PALETTE["muted"],
        anchor="e",
    ).pack(side="right")

    wert = tk.Label(
        karte,
        text="000 / 100",
        font=("Bahnschrift SemiBold", 22),
        bg=karte.cget("bg"),
        fg=PALETTE["text"],
        anchor="w",
    )
    wert.pack(fill="x", pady=(8, 8))

    progress = tk.Canvas(
        karte,
        height=18,
        bg=PALETTE["track"],
        highlightthickness=1,
        highlightbackground=PALETTE["panel_border"],
        bd=0,
    )
    progress.pack(fill="x")

    daten = {
        "progress": progress,
        "value_label": wert,
        "variable": variable,
        "accent": accent,
    }

    progress.bind("<Configure>", lambda event, target=daten: aktualisiere_bar(target, variable.get()))
    variable.trace_add("write", lambda *_args, target=daten, source=variable: aktualisiere_bar(target, source.get()))

    return daten


def aktualisiere_bar(bar: dict[str, tk.Widget | tk.IntVar | str], wert: int) -> None:
    progress = bar.get("progress")
    label = bar["value_label"]
    accent = bar["accent"]

    if not isinstance(progress, tk.Canvas) or not isinstance(label, tk.Label) or not isinstance(accent, str):
        return

    wert = max(0, min(100, int(wert)))
    label.config(text=f"{wert:03d} / 100")

    breite = max(progress.winfo_width(), 60)
    hoehe = max(progress.winfo_height(), 18)
    fuellbreite = int((breite - 4) * (wert / 100))

    progress.delete("all")
    progress.create_rectangle(2, 2, breite - 2, hoehe - 2, outline="", fill=PALETTE["track"])

    for x_wert in range(12, breite, 22):
        progress.create_line(x_wert, 3, x_wert, hoehe - 3, fill=PALETTE["grid_soft"])

    if fuellbreite > 0:
        progress.create_rectangle(2, 2, 2 + fuellbreite, hoehe - 2, outline="", fill=accent)
        progress.create_rectangle(max(2 + fuellbreite - 12, 2), 2, 2 + fuellbreite, hoehe - 2, outline="", fill="#E8FBFF")


def zeige_zeile(elternteil: tk.Widget, titel: str, wert: str, umbruch: int = 0) -> tk.Label:
    container = panel_card(elternteil)
    container.pack(fill="x", pady=5)

    kopf = tk.Frame(container, bg=PALETTE["panel_alt"])
    kopf.pack(fill="x")

    tk.Label(
        kopf,
        text=titel,
        font=("Bahnschrift SemiBold", 10),
        bg=PALETTE["panel_alt"],
        fg=PALETTE["amber"],
        anchor="w",
        justify="left",
    ).pack(side="left")

    tk.Label(
        kopf,
        text="::",
        font=("Consolas", 10, "bold"),
        bg=PALETTE["panel_alt"],
        fg=PALETTE["muted"],
    ).pack(side="right")

    wert_label = tk.Label(
        container,
        text=wert,
        font=("Bahnschrift", 11),
        bg=PALETTE["panel_alt"],
        fg=PALETTE["text"],
        anchor="w",
        justify="left",
        wraplength=umbruch,
    )
    wert_label.pack(fill="x", pady=(6, 0))

    return wert_label


def erstelle_statuskachel(elternteil: tk.Widget, titel: str, zeile: int, spalte: int) -> tk.Label:
    kachel = panel_card(elternteil)
    kachel.grid(row=zeile, column=spalte, padx=5, pady=5, sticky="nsew")

    tk.Label(
        kachel,
        text=titel,
        font=("Consolas", 10, "bold"),
        bg=PALETTE["panel_alt"],
        fg=PALETTE["muted"],
        anchor="w",
    ).pack(fill="x")

    tk.Frame(kachel, bg=PALETTE["grid"], height=1).pack(fill="x", pady=(8, 8))

    wert_label = tk.Label(
        kachel,
        text="-",
        font=("Bahnschrift SemiBold", 14),
        bg=PALETTE["panel_alt"],
        fg=PALETTE["text"],
        anchor="w",
    )
    wert_label.pack(fill="x")

    return wert_label


def zeichne_gridstrip(canvas: tk.Canvas) -> None:
    breite = max(canvas.winfo_width(), 120)
    hoehe = max(canvas.winfo_height(), 14)
    canvas.delete("all")
    for x_wert in range(0, breite, 24):
        canvas.create_line(x_wert, 0, x_wert + 12, hoehe, fill=PALETTE["scanline"])
    canvas.create_line(0, hoehe - 2, breite, hoehe - 2, fill=PALETTE["grid"])


def zeichne_panel_ecken(widget: tk.Widget) -> None:
    overlay = getattr(widget, "_hud_overlay", None)
    if overlay is None:
        overlay = tk.Canvas(widget, bg=widget.cget("bg"), highlightthickness=0, bd=0)
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        overlay.tk.call("lower", overlay._w)
        widget._hud_overlay = overlay

    breite = max(widget.winfo_width(), 20)
    hoehe = max(widget.winfo_height(), 20)
    laenge = 12

    overlay.config(width=breite, height=hoehe)
    overlay.delete("all")
    overlay.create_line(1, 1, laenge, 1, fill=PALETTE["grid"], width=2)
    overlay.create_line(1, 1, 1, laenge, fill=PALETTE["grid"], width=2)
    overlay.create_line(breite - laenge, 1, breite - 1, 1, fill=PALETTE["grid"], width=2)
    overlay.create_line(breite - 1, 1, breite - 1, laenge, fill=PALETTE["grid"], width=2)
    overlay.create_line(1, hoehe - 1, laenge, hoehe - 1, fill=PALETTE["grid"], width=2)
    overlay.create_line(1, hoehe - laenge, 1, hoehe - 1, fill=PALETTE["grid"], width=2)
    overlay.create_line(breite - laenge, hoehe - 1, breite - 1, hoehe - 1, fill=PALETTE["grid"], width=2)
    overlay.create_line(breite - 1, hoehe - laenge, breite - 1, hoehe - 1, fill=PALETTE["grid"], width=2)


def visualisiere_zustand(stresslevel: int, energielevel: int, fokuslevel: int) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        messagebox.showerror(
            "Matplotlib Missing",
            "Matplotlib is not installed.\nInstall it with: pip install matplotlib",
        )
        return

    hud_bg = "#050A14"
    neon_cyan = "#00F5FF"
    glow_white = "#D9FEFF"
    grid_cyan = (0 / 255, 245 / 255, 255 / 255, 0.16)
    pane_cyan = (0.0, 0.0, 0.0, 0.0)

    plt.close("State Space")
    figure = plt.figure("State Space", figsize=(9, 7), facecolor=hud_bg)
    figure.patch.set_facecolor(hud_bg)
    achse = figure.add_subplot(111, projection="3d")
    achse.set_facecolor(hud_bg)

    pane_axes = [
        getattr(achse, "xaxis", None),
        getattr(achse, "yaxis", None),
        getattr(achse, "zaxis", None),
    ]
    for axis in pane_axes:
        if axis is None:
            continue
        if hasattr(axis, "set_pane_color"):
            axis.set_pane_color(pane_cyan)
        if hasattr(axis, "_axinfo"):
            axis._axinfo["grid"]["color"] = grid_cyan
            axis._axinfo["grid"]["linewidth"] = 0.8
            axis._axinfo["axisline"]["color"] = neon_cyan
            axis._axinfo["tick"]["color"] = neon_cyan

    if hasattr(achse, "w_xaxis"):
        achse.w_xaxis.line.set_color(neon_cyan)
        achse.w_yaxis.line.set_color(neon_cyan)
        achse.w_zaxis.line.set_color(neon_cyan)

    kugel_radius = 100
    u_werte = np.linspace(0, 2 * np.pi, 48)
    v_werte = np.linspace(0, np.pi, 24)
    kugel_x = kugel_radius * np.outer(np.cos(u_werte), np.sin(v_werte))
    kugel_y = kugel_radius * np.outer(np.sin(u_werte), np.sin(v_werte))
    kugel_z = kugel_radius * np.outer(np.ones_like(u_werte), np.cos(v_werte))

    achse.plot_surface(
        kugel_x,
        kugel_y,
        kugel_z,
        color=neon_cyan,
        alpha=0.05,
        linewidth=0,
        shade=False,
        antialiased=True,
        zorder=0,
    )

    achse.scatter(
        [0],
        [0],
        [0],
        s=26,
        c=neon_cyan,
        alpha=0.35,
        edgecolors="none",
        depthshade=False,
    )

    achse.scatter(
        [stresslevel],
        [energielevel],
        [fokuslevel],
        s=1100,
        c=neon_cyan,
        alpha=0.16,
        edgecolors="none",
        depthshade=False,
    )
    achse.scatter(
        [stresslevel],
        [energielevel],
        [fokuslevel],
        s=420,
        c=neon_cyan,
        alpha=0.32,
        edgecolors="none",
        depthshade=False,
    )
    achse.scatter(
        [stresslevel],
        [energielevel],
        [fokuslevel],
        s=120,
        c=neon_cyan,
        edgecolors=glow_white,
        linewidths=1.2,
        depthshade=False,
    )
    achse.plot(
        [0, stresslevel],
        [0, energielevel],
        [0, fokuslevel],
        color=neon_cyan,
        linewidth=6.5,
        alpha=0.12,
        solid_capstyle="round",
    )
    achse.plot(
        [0, stresslevel],
        [0, energielevel],
        [0, fokuslevel],
        color=neon_cyan,
        linewidth=1.8,
        alpha=0.95,
        solid_capstyle="round",
    )

    achse.set_title("STATE VECTOR ANALYSIS", color=neon_cyan, fontsize=18, fontweight="bold", pad=18)
    achse.set_xlabel("STRESS", color=neon_cyan, fontsize=12, fontweight="bold", labelpad=12)
    achse.set_ylabel("ENERGY", color=neon_cyan, fontsize=12, fontweight="bold", labelpad=12)
    achse.set_zlabel("FOCUS", color=neon_cyan, fontsize=12, fontweight="bold", labelpad=12)
    achse.set_xlim(-100, 100)
    achse.set_ylim(-100, 100)
    achse.set_zlim(-100, 100)
    achse.set_xticks(range(-100, 101, 50))
    achse.set_yticks(range(-100, 101, 50))
    achse.set_zticks(range(-100, 101, 50))
    achse.tick_params(colors=neon_cyan, labelsize=10)
    achse.grid(True)
    achse.view_init(elev=22, azim=42)

    plt.tight_layout()
    plt.show()


def ist_matplotlib_verfuegbar() -> bool:
    return importlib.util.find_spec("matplotlib") is not None


def ermittle_ui_farben(zustand: str, fallback_hex: str) -> dict[str, str]:
    return STATE_UI_ACCENTS.get(
        zustand.strip().lower(),
        {"accent": fallback_hex, "surface": PALETTE["panel_alt"], "badge": "ACTIVE"},
    )


def mische_farbe(start_hex: str, ziel_hex: str, anteil: float) -> str:
    start_rgb = hex_zu_rgb(start_hex)
    ziel_rgb = hex_zu_rgb(ziel_hex)

    gemischt = []
    for start_wert, ziel_wert in zip(start_rgb, ziel_rgb):
        wert = round(start_wert + (ziel_wert - start_wert) * anteil)
        gemischt.append(wert)

    return rgb_zu_hex(tuple(gemischt))


def hex_zu_rgb(farbe_hex: str) -> tuple[int, int, int]:
    farbe_hex = farbe_hex.lstrip("#")
    return (
        int(farbe_hex[0:2], 16),
        int(farbe_hex[2:4], 16),
        int(farbe_hex[4:6], 16),
    )


def rgb_zu_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def ermittle_textfarbe(farbe_hex: str) -> str:
    rot, gruen, blau = hex_zu_rgb(farbe_hex)
    helligkeit = (rot * 299 + gruen * 587 + blau * 114) / 1000
    return "#071019" if helligkeit > 170 else "#F4FBFF"
