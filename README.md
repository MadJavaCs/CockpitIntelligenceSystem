# CockpitIntelligenceSystem

## Demo-Checkliste

1. Backend starten: `python main.py`
2. UI im Browser öffnen: `index.html`
3. Home Assistant öffnen und Ziel-Entitäten prüfen
4. Health Check testen: Backend- und Home-Assistant-Verbindung prüfen
5. `Recalculate State` klicken und Risk Index / Driver State beobachten
6. Verhalten prüfen: `Kritisch`, `Muede`, `Wachsam/Stabil`
7. MQTT Event Bus Card prüfen:
   - Status: `Simulated Event Bus`
   - Topic: `porsche/driver/state`
   - Last Event entspricht aktuellem Driver State
   - Payload enthält `driverState`, `drivingMode`, `riskIndex`, `timestamp`
