# Projektdokumentation

## Porsche Cockpit Intelligence System

---

## Deckblatt

**Titel der Arbeit:**  
Porsche Cockpit Intelligence System

**Untertitel:**  
Konzeption und prototypische Entwicklung eines Assistenzsystems zur Analyse des Fahrerzustands und zur Ableitung eines dynamischen Fahrmodus

**Art der Arbeit:**  
Projektdokumentation

**Name:**  
[Name eintragen]

**Matrikelnummer:**  
[Matrikelnummer eintragen]

**Studiengang:**  
[Studiengang eintragen]

**Modul / Veranstaltung:**  
[Modul oder Veranstaltung eintragen]

**Betreuende Lehrperson:**  
[Name eintragen]

**Abgabedatum:**  
22. April 2026

**Hinweis zur Formatierung in Word:**  
Für die finale Abgabe empfiehlt sich:

- Schriftart `Times New Roman` oder `Calibri`
- Schriftgröße `12 pt`
- Zeilenabstand `1,5`
- Blocksatz
- Seitenränder `2,5 cm`
- automatische Überschriftenformatierung für Verzeichnisse

---

**Seitenumbruch für Word einfügen**

---

## Abstract

Die vorliegende Arbeit dokumentiert die Konzeption, Entwicklung und den aktuellen Stand des prototypischen Systems `Porsche Cockpit Intelligence System`. Ziel des Projekts war die Entwicklung eines fahrerzustandsbasierten Assistenzsystems, das zentrale Zustandsgrößen des Fahrers analysiert, diese zu einem Risk Index verdichtet und auf dieser Grundlage einen situationsabhängigen Fahrmodus ableitet. Im Zentrum standen die Größen `Stress`, `Energy`, `Focus` sowie die im Entwicklungsverlauf ergänzte Variable `Ablenkung`.

Die Arbeit verfolgt dabei nicht ausschließlich eine beschreibende Perspektive, sondern legt besonderen Wert auf die Begründung der getroffenen technischen und gestalterischen Entscheidungen. Im Fokus stehen folglich nicht nur die implementierten Funktionen, sondern auch die Frage, weshalb bestimmte Modellierungsansätze gewählt, welche Entwicklungsschritte durchlaufen und auf welche Weise konkrete Probleme identifiziert und gelöst wurden. Hierzu zählen insbesondere die Ausdifferenzierung der Risikologik, die zunehmende Erklärbarkeit systemischer Entscheidungen sowie die Überarbeitung des visuellen Designs der Human-Machine-Interface-Struktur.

Im Ergebnis zeigt sich, dass das Projekt über die reine Implementierung eines Dashboards hinausgeht. Vielmehr entstand ein in sich schlüssiger Demonstrator, der Zustandsanalyse, Risikobewertung, Fahrmodusableitung und cockpitnahe Interaktionsgestaltung zu einem argumentativ nachvollziehbaren Gesamtsystem verbindet. Die Arbeit macht damit deutlich, wie fahrerbezogene Daten in einem prototypischen Assistenzkontext systematisch interpretiert und zugleich hochwertig visualisiert werden können.

**Schlüsselwörter:**  
Fahrerzustandsanalyse, Risk Index, Assistenzsystem, Human-Machine Interface, Fahrmodus, Prototyping

---

**Seitenumbruch für Word einfügen**

---

## Inhaltsverzeichnis

1. Einleitung  
2. Konzept und Systemidee  
3. Entwicklungsverlauf  
4. Systemlogik  
5. UI- und HMI-Design  
6. Technische Umsetzung  
7. Herausforderungen und Lösungsansätze  
8. Ergebnis und aktueller Stand  
9. Reflexion und Weiterentwicklung  
10. Fazit  
11. Literatur- und Quellenverzeichnis  
12. Abbildungsverzeichnis  
13. Anhang  

**Hinweis:**  
In Word sollte dieses manuelle Inhaltsverzeichnis durch ein automatisches Verzeichnis auf Basis der Überschriften ersetzt werden.

---

**Seitenumbruch für Word einfügen**

---

## 1. Einleitung

### 1.1 Motivation
Moderne Fahrzeuge verfügen über eine stetig wachsende Anzahl sensorischer und softwarebasierter Systeme zur Erfassung von Fahrzeug- und Umgebungszuständen. Demgegenüber wird der Zustand des Fahrers in vielen Assistenzkonzepten weiterhin nur eingeschränkt oder lediglich indirekt berücksichtigt. Genau an dieser Stelle setzt das vorliegende Projekt an. Das Porsche Cockpit Intelligence System verfolgt den Ansatz, fahrerbezogene Zustandsinformationen nicht nur sichtbar zu machen, sondern sie in eine nachvollziehbare, adaptive Assistenzlogik zu überführen.

Ausgangspunkt des Projekts war die Beobachtung, dass eine reine Anzeige von Messwerten im fahrdynamischen Kontext nur begrenzten Mehrwert bietet. Erst die interpretative Einordnung dieser Werte ermöglicht eine Systemreaktion, die situationsangemessen, erklärbar und für den Nutzer sinnvoll erfassbar ist. Ein Fahrer mit hoher Energiereserve und stabilem Fokus benötigt eine andere Form der Unterstützung als ein Fahrer, der sich während einer Nachtfahrt in einem ermüdungsnahen oder kognitiv belasteten Zustand befindet. Die Entwicklung eines Systems, das diese Unterschiede systematisch erfasst und in Handlungslogik übersetzt, bildete daher den konzeptionellen Ausgangspunkt.

### 1.2 Problemstellung
Im Kontext moderner Fahrerassistenz ergibt sich das grundlegende Problem, dass sicherheitsrelevante Veränderungen des Fahrerzustands häufig erst dann sichtbar werden, wenn bereits eine merkliche Leistungsminderung eingetreten ist. Konventionelle Anzeigen oder statische Warnmechanismen reagieren in solchen Situationen oft zu spät oder bleiben in ihrer Aussagekraft zu abstrakt, da sie zwar Parameter ausgeben, jedoch keinen interpretativen Zusammenhang zwischen Zustand, Risiko und Systemreaktion herstellen.

Vor diesem Hintergrund ergaben sich für das Projekt drei zentrale Fragestellungen:

- Wie lässt sich der Fahrerzustand in ein kompaktes, zugleich aber differenziert interpretierbares Modell überführen?
- Wie kann aus mehreren Einflussgrößen ein plausibler und nachvollziehbarer Risk Index abgeleitet werden?
- Wie muss eine HMI gestaltet sein, um komplexe Zustands- und Entscheidungslogik im Cockpitkontext präzise, hierarchisch klar und visuell hochwertig darzustellen?

### 1.3 Zielsetzung
Ziel des Projekts war die Entwicklung eines prototypischen Assistenzsystems, das drei funktionale Schwerpunkte miteinander verbindet:

- Analyse des Fahrerzustands auf Basis der Größen `Stress`, `Energy`, `Focus` und später `Ablenkung`
- Verdichtung dieser Eingaben zu einem `Risk Index`
- Ableitung eines dynamischen Fahrmodus wie `Komfort`, `Adaptiv` oder `Warnmodus`

Darüber hinaus bestand eine wesentliche Zielsetzung darin, die Systementscheidungen nicht als intransparente Resultate erscheinen zu lassen, sondern als nachvollziehbare Folge bewusst modellierter Zusammenhänge. Das Projekt versteht sich somit nicht nur als technische Demonstration, sondern als prototypische Ausarbeitung eines argumentativ belastbaren Assistenzkonzepts.

## 2. Konzept und Systemidee

### 2.1 Grundidee des Assistenzsystems
Die Grundidee des Systems besteht darin, den Fahrerzustand als aktive Entscheidungsvariable innerhalb der Fahrzeuglogik zu behandeln. An die Stelle einer isolierten Darstellung einzelner Messwerte tritt ein interpretatives Modell, das mehrere Eingangsparameter zusammenführt und daraus eine begründete Assistenzreaktion ableitet. Das System beantwortet damit nicht allein die Frage nach dem aktuellen Zustand des Fahrers, sondern vor allem die Frage, welche Reaktion des Fahrzeugs unter den gegebenen Bedingungen sachlich angemessen ist.

Die Systemarchitektur folgt dabei einem bewusst reduzierten, aber methodisch nachvollziehbaren Schema:

1. Kontext- und Eingangsdaten werden aus Zeit, Fahrkontext, Wetter sowie fahrerbezogenen Parametern gebildet.
2. Daraus werden Zustandswerte für Stress, Energie und Fokus erzeugt oder simulativ hergeleitet.
3. Eine Risikologik verdichtet diese Faktoren zu einer numerischen Kennzahl.
4. Auf Grundlage dieser Kennzahl werden Fahrerzustand, Warnstufe und Fahrmodus abgeleitet.
5. Die HMI überführt diese Entscheidung in eine strukturierte visuelle Cockpit-Darstellung.

### 2.2 Zusammenhang zwischen Fahrerzustand und Fahrmodus
Der Zusammenhang zwischen Fahrerzustand und Fahrmodus bildet den fachlichen Kern des Systems. Die zugrunde liegende Annahme lautet, dass fahrerbezogene Belastung nicht nur beobachtet, sondern in eine situationsabhängige Assistenzreaktion übersetzt werden sollte. Der Fahrmodus fungiert folglich nicht als dekoratives Merkmal, sondern als Ergebnis einer regelbasierten Interpretation des Zustandsraums.

Im prototypischen Modell bedeutet dies:

- Ein stabiler Zustand mit niedrigem Risiko führt zu `Komfort`.
- Ein erhöhter, aber noch kontrollierbarer Zustand führt zu `Adaptiv`.
- Ein deutlich kritischer Zustand führt zu `Warnmodus` beziehungsweise im erweiterten System zu `Warnbetrieb` oder `Interventionsmodus`.

Diese Zuordnung wurde bewusst regelbasiert entwickelt. Für einen Prototypen ist eine explizit modellierte, verbal und technisch nachvollziehbare Logik einem schwer erklärbaren Black-Box-Ansatz vorzuziehen, da nur auf dieser Grundlage Entwicklungsentscheidungen transparent reflektiert werden können.

### 2.3 Relevanz im Kontext moderner Fahrzeuge
Das System ist insbesondere vor dem Hintergrund moderner, softwaredefinierter Fahrzeuge relevant. Sein Mehrwert liegt in drei Aspekten:

- Es verknüpft fahrerbezogene Innenraumdaten mit situativem Fahrkontext.
- Es ermöglicht eine frühzeitige, kontextsensitiv abgeleitete Intervention.
- Es demonstriert, wie komplexe Zustandslogik innerhalb einer hochwertigen HMI reduziert und zugleich erklärbar dargestellt werden kann.

Gerade im Premiumsegment ist diese Verknüpfung von Funktionalität, Interaktionsqualität und Markenanmutung von besonderer Bedeutung. Ein System dieser Art muss nicht nur korrekt reagieren, sondern seine Reaktion auch auf eine Weise kommunizieren, die den Anspruch eines hochwertigen Cockpit-Erlebnisses einlöst.

## 3. Entwicklungsverlauf

### 3.1 Projektbeginn am 23.03
Der Projektbeginn markierte die konzeptionelle Phase, in der zunächst die Frage der Modellierbarkeit des Fahrerzustands im Vordergrund stand. Noch bevor konkrete HMI-Entscheidungen getroffen wurden, musste geklärt werden, welche Größen für eine sinnvolle und zugleich handhabbare Beschreibung des Fahrerzustands geeignet sind. Frühzeitig wurde entschieden, nicht mit einer großen Zahl lose gekoppelter Parameter zu arbeiten, sondern mit wenigen, fachlich gut begründbaren Kernvariablen:

- `Stress` als Indikator mentaler Belastung
- `Energy` als Indikator für Ermüdung und Leistungsreserve
- `Focus` als Indikator für Aufmerksamkeitsstabilität

Diese Reduktion stellte eine bewusste methodische Entscheidung dar. Ein umfangreicheres Modell wäre zwar grundsätzlich denkbar gewesen, hätte für den Prototypen jedoch nur begrenzten Erkenntnisgewinn geliefert und zugleich die spätere Erklärbarkeit deutlich erschwert. Bereits in dieser frühen Phase wurde außerdem festgelegt, dass das Projekt nicht auf eine rein dekorative Visualisierung abzielen sollte, sondern auf ein Assistenzsystem, dessen Entscheidungen aus der inneren Logik des Modells heraus argumentierbar sind.

### 3.2 Erster Prototyp bis 31.03
Der erste Prototyp diente primär der technischen Verifikation der Grundidee. Die vorliegende Projektstruktur legt nahe, dass diese Entwicklungsphase zunächst stark Python-basiert war. Mit `start.bat`, einer zentralen Programmlogik und der später vorhandenen Desktop-Oberfläche in `ui.py` wurde ein funktionaler Demonstrator aufgebaut, in dem Analyse, Zustandsbewertung und Ausgabe noch vergleichsweise eng miteinander verbunden waren.

Ziel dieser Phase war weniger die gestalterische Ausdifferenzierung als vielmehr die Klärung grundlegender Funktionsfragen:

- Lassen sich zeitliche und situative Eingaben konsistent verarbeiten?
- Kann aus diesen Eingaben ein plausibler Fahrerzustand abgeleitet werden?
- Ist die resultierende Bewertung in ihrer Grundstruktur für Dritte nachvollziehbar?

Die Priorisierung der funktionalen Plausibilisierung gegenüber dem visuellen Feinschliff war in dieser Phase konsequent. Erst nachdem die Grundlogik als tragfähig bewertet werden konnte, war eine gestalterische Weiterentwicklung sinnvoll.

### 3.3 Frühe Iteration: Von der Zustandsanzeige zur kontextsensitiven Bewertung
Im weiteren Verlauf wurde die Systemlogik deutlich differenzierter. Aus einer zunächst eher direkten Zustandszuordnung entwickelte sich schrittweise eine regelbasierte Bewertung, in der Fahrkontext, Wetter, Tageszeit und später auch Temperatur systematisch miteinander verknüpft wurden.

Ein zentraler Entwicklungsschritt bestand darin, Telemetriedaten nicht nur manuell vorzugeben, sondern aus dem situativen Kontext herzuleiten. In `logic.py` zeigt die Funktion `calculate_telemetry(...)`, dass Uhrzeit, Fahrkontext, Wetter und Außentemperatur zur Erzeugung der Werte für Stress, Energie und Fokus herangezogen werden. Diese Entscheidung war fachlich wesentlich, weil das System dadurch den Charakter eines kontextsensitiven Assistenzmodells annimmt und nicht auf die Logik eines isolierten Kennzahlenrechners reduziert bleibt.

Im Rahmen dieser Iteration wurden unter anderem folgende Zusammenhänge bewusst modelliert:

- erhöhter Stress im Stadtverkehr
- sinkende Energie und sinkender Fokus während der Nachtfahrt
- zusätzliche Belastung infolge von Nebel, Regen, Wind oder Sturm
- Anpassungen in Abhängigkeit von der Außentemperatur

Damit verlagerte sich das Projekt von einer reinen Zustandsvisualisierung hin zu einem plausiblen Simulations- und Interpretationssystem.

### 3.4 Ausdifferenzierung der Moduslogik
Ein weiterer wesentlicher Entwicklungsschritt bestand in der Ausdifferenzierung der Fahr- und Assistenzmodi. Die Funktion `evaluate_context(...)` verdeutlicht, dass die interne Systemlogik nicht bei einer einzigen Warnstufe verbleibt, sondern mehrere Assistenzprofile wie `Schutzmodus`, `Ruhiger Modus`, `Stabilisierung`, `Warnmodus`, `Wachsamkeit`, `Erholung` oder `Ausgleich` umfasst.

Diese Ausdifferenzierung löste ein zentrales fachliches Problem. Ein einzelner globaler Modus hätte sehr unterschiedliche Situationen nur unzureichend abbilden können. Ein müder Fahrer während einer Nachtfahrt benötigt eine andere Art der Systemreaktion als ein gestresster Fahrer im dichten Stadtverkehr oder ein Fahrer mit monotoniebedingtem Aufmerksamkeitsabfall auf der Autobahn. Die Mehrzahl der Modi wurde daher bewusst eingeführt, um den Prototypen sowohl in seiner Differenzierungsfähigkeit als auch in seiner argumentativen Plausibilität zu stärken.

Gleichzeitig blieb für die spätere Web-HMI eine reduzierte, nach außen klar kommunizierbare Darstellung mit `Komfort`, `Adaptiv` und `Warnmodus` erhalten. Auch diese Trennung zwischen interner und externer Logik war eine bewusste Entwurfsentscheidung: Die Systemlogik darf intern komplexer sein, solange ihre Außenwirkung in einer übersichtlichen und intuitiv erfassbaren Darstellung resultiert.

### 3.5 Aufbau einer frühen Desktop-Oberfläche
Mit der Python-Datei `ui.py`, deren Zeitstempel auf den 13.04 verweist, wurde eine umfangreiche Desktop-Oberfläche entwickelt. Diese Fassung dokumentiert, dass bereits vor der finalen Web-HMI eine ausgeprägte gestalterische Richtung vorhanden war. Sichtbar werden insbesondere:

- eine futuristische HUD-Anmutung
- farbcodierte Warn- und Zustandsdarstellungen
- textliche Interpretation von Systementscheidungen
- strukturierte Felder für Kontext, Fahrerzustand und Bewertung

Die Desktop-Variante ist als wichtiger Zwischenschritt zu verstehen. Sie ermöglichte es, die Wirkungszusammenhänge der Logik in einer konkreten Darstellung zu erproben, bevor die modernere Browser-HMI realisiert wurde. Aus entwicklungstechnischer Perspektive war dies sinnvoll, weil Logik, Informationsstruktur und visuelle Gewichtung früh getestet werden konnten, ohne bereits alle Anforderungen eines webbasierten Interfaces vollständig auszuformulieren.

Die Entwicklungslinie vom funktionsorientierten Zwischenstand zur späteren webbasierten HMI lässt sich an dieser Stelle auch visuell nachvollziehen; im Fließtext kann dies über `vgl. Abbildung 1` referenziert werden.

**[Abbildung 1 hier einfügen: Frühere Desktop-Oberfläche des Systems als Zwischenstand der visuellen Entwicklung]**

### 3.6 Integration neuer Kontextquellen
Am 20.04 wurden mit `state.py` und `home_assistant.py` neue strukturelle Elemente eingeführt. Dies verweist auf eine Entwicklungsphase, in der das System von einer ausschließlich lokalen Demonstration zu einem kontextoffeneren Assistenzprototyp erweitert wurde.

Von besonderer Bedeutung war dabei die vorbereitete `Home Assistant`-Anbindung. Auch wenn die aktuelle Implementierung mit Beispieldaten arbeitet, markiert sie einen wesentlichen konzeptionellen Fortschritt:

- Zeitkontext kann extern bereitgestellt werden.
- Fahrkontext und Wetter müssen nicht ausschließlich lokal simuliert werden.
- Zusatzinformationen wie Kalenderstatus oder Gerätezustand können in die HMI integriert werden.

Mit dieser Erweiterung wurde bewusst der Schritt von einer geschlossenen Demo-Logik hin zu einem potenziell vernetzten Cockpit-System vollzogen.

### 3.7 Einführung von Ablenkung als expliziter Risikotreiber
Ein besonders relevanter qualitativer Entwicklungsschritt war die Einführung von `Ablenkung` als eigenständiger Faktor innerhalb der Risikologik. Technisch wird dieser in der aktuellen Version über den Fokuswert abgeleitet:

- `Focus < 30` -> `stark abgelenkt` mit `+15`
- `Focus < 60` -> `abgelenkt` mit `+8`
- ansonsten `keine Ablenkung` mit `+0`

Diese Erweiterung war deshalb notwendig, weil ein niedriger Fokuswert zwar eine Verschlechterung des Zustands anzeigt, die konkrete Interpretation als Ablenkungsrisiko jedoch noch nicht explizit sichtbar macht. Erst durch die zusätzliche Übersetzung in einen eigenständigen Ablenkungsstatus wurde die Logik sowohl aus Systemsicht als auch aus Darstellungssicht deutlich aussagekräftiger.

Fachlich löste diese Erweiterung zwei Probleme:

- Der Zusammenhang zwischen nachlassendem Fokus und steigendem Risiko wurde explizit ausgewiesen.
- Der Risk Index erhielt einen zusätzlichen, unmittelbar nachvollziehbaren Modifikator.

### 3.8 Konsolidierung des Risk Index als begründete Kennzahl
Mit der weiteren Projektentwicklung wurde der Risk Index zunehmend von einer bloßen Anzeigezahl zu einer begründeten, offen kommunizierten Kennzahl ausgearbeitet. In `logic.py` basiert die aktuelle Berechnung auf einer gewichteten Formel:

- `Stress * 0.45`
- `(100 - Energy) * 0.35`
- `(100 - Focus) * 0.20`
- `Ablenkungsaufschlag`
- Zufallsoffset im Bereich `-5` bis `+5`

Die Gewichtung der Faktoren ist bewusst asymmetrisch angelegt. Stress stellt den stärksten unmittelbaren Treiber dar, gefolgt von sinkender Energie und sinkendem Fokus. Diese Priorisierung ist fachlich plausibel, da akute mentale Überlastung im Fahrzeugkontext besonders schnell in instabiles Verhalten übergehen kann.

Von wesentlicher Bedeutung war zudem die Einführung einer formatierten Risikoformel innerhalb der Ausgabe. Dadurch wird nicht nur ein Endwert präsentiert, sondern zugleich die innere Struktur der Berechnung sichtbar gemacht. Diese Entscheidung erhöht die Nachvollziehbarkeit des Systems erheblich und ist insbesondere für eine akademische Dokumentation von zentraler Bedeutung.

### 3.9 Übergang zur webbasierten HMI am 22.04
Am 22.04 wurde mit `main.py`, `script.js`, `index.html` und `style.css` eine moderne Browser-HMI eingeführt. Dieser Schritt stellte keinen bloßen Technologiewechsel dar, sondern markierte eine grundlegende Neuausrichtung der Präsentation und Interaktion. Charakteristisch für diese Phase sind:

- eine stärker ausgeprägte Dashboard-Struktur
- klar gegliederte modulare Panels
- interaktive Szenario-Simulation
- die visuelle Verdichtung auf einen zentralen Risk-Meter
- erweiterte Erklärungsketten für Ursache, Analyse, Entscheidung und Aktion

Mit dieser Umstellung wurde ein wesentliches Defizit früherer Versionen adressiert: Informationen wurden nicht mehr nur dargestellt, sondern in eine visuelle Informationshierarchie überführt. Gerade diese Hierarchisierung war notwendig, um die Systemlogik nicht nur technisch korrekt, sondern auch präsentationsfähig und für externe Betrachter intuitiv nachvollziehbar zu machen.

Die strukturelle Verdichtung dieses Entwicklungsstands wird besonders deutlich in der Gesamtansicht der webbasierten Oberfläche; im Text kann dies über `vgl. Abbildung 2` referenziert werden.

**[Abbildung 2 hier einfügen: Gesamtansicht der webbasierten Cockpit-Oberfläche mit Dashboard-Struktur]**

### 3.10 Iterative Verbesserung der Erklärbarkeit
Ein auffälliger Entwicklungsschritt der aktuellen Webversion liegt in der deutlich erweiterten Erklärung systemischer Entscheidungen. Die Oberfläche beschränkt sich nicht auf Werteanzeigen, sondern integriert zusätzlich:

- `Assistenzreaktion`
- `Systementscheidung`
- `Ursache`, `Analyse` und `Entscheidung`
- eine `Decision Chain` mit Input, Analyse, Entscheidung und Aktion

Diese Struktur wurde erkennbar bewusst eingeführt, um eine Black-Box-Wirkung zu vermeiden. Gerade in einem akademischen Kontext ist es unzureichend, wenn ein System zwar Entscheidungen trifft, deren Herleitung jedoch nicht ersichtlich wird. Die explizite Sichtbarmachung der Entscheidungslogik stellt daher einen wesentlichen qualitativen Fortschritt dar.

Besonders anschaulich wird diese Entwicklung in der Entscheidungskette der Oberfläche, welche Eingabe, Analyse, Systementscheidung und resultierende Aktion in eine klar lesbare Sequenz überführt; dies kann im Fließtext über `vgl. Abbildung 5` belegt werden.

**[Abbildung 5 hier einfügen: Entscheidungskette aus Input, Analyse, Entscheidung und Aktion]**

### 3.11 UI-Verbesserungen und visuelle Bereinigung
Parallel zur funktionalen Erweiterung wurde die Web-HMI auch visuell gezielt bereinigt. Besonders aussagekräftig ist in diesem Zusammenhang die Überarbeitung des zentralen Radialmeters für den Risk Index.

In `style.css` ist erkennbar, dass im Bereich von `.driver-panel`, `.radial-cluster`, `.radial-stack` und `#risk-meter` mehrere visuelle Effekte explizit deaktiviert wurden:

- `background: transparent !important`
- `box-shadow: none !important`
- `filter: none !important`
- Deaktivierung von `::before`- und `::after`-Pseudo-Elementen
- Entfernung zusätzlicher Glow-Flächen im Hintergrund

Diese Maßnahmen verweisen unmittelbar auf einen zuvor aufgetretenen Darstellungsfehler, insbesondere auf den beschriebenen quadratischen Glow-Effekt hinter einem kreisförmigen Anzeigeelement. Das Problem ist für komplexe CSS-basierte HMI-Strukturen charakteristisch: Auch wenn das sichtbare Kernelement kreisförmig gestaltet ist, können umgebende Container, Pseudo-Elemente oder Schatteneffekte weiterhin rechteckige Flächen erzeugen und damit die visuelle Klarheit erheblich stören.

Gerade die visuelle Relevanz dieses Problems lässt sich über eine Gegenüberstellung des Zustands vor und nach der Bereinigung dokumentieren; ein entsprechender Fließtextverweis kann als `vgl. Abbildung 10` formuliert werden.

**[Abbildung 10 hier einfügen: Vergleich des Radialmeters vor und nach der Korrektur des quadratischen Glow-Effekts]**

### 3.12 Analyse und Lösung des quadratischen Glow-Bugs
Der quadratische Glow-Bug war nicht lediglich ein kosmetischer Mangel, sondern ein Problem mit direkter Auswirkung auf die wahrgenommene Qualität der Schnittstelle. Ein zentrales Anzeigeelement verliert an Präzision und Wertigkeit, wenn sich hinter seiner eigentlich runden Form rechteckige Leuchtflächen abzeichnen.

Die Problemlösung erfolgte systematisch:

1. Identifikation des sichtbaren Fehlers am zentralen Risk-Meter
2. Prüfung, ob die Ursache im SVG selbst oder in den umgebenden CSS-Layern liegt
3. Ausschluss der SVG-Ebene als primäre Fehlerquelle
4. Rückverfolgung auf Hintergrundflächen, Schatten, Filter und Pseudo-Elemente der Containerstruktur
5. gezielte Neutralisierung aller störenden visuellen Ebenen

Die gewählte Lösung war bewusst konsequent. Anstatt einzelne Parameter lediglich zu reduzieren, wurden alle potenziell störenden Layer im unmittelbaren Umfeld des Meters entfernt. Dadurch entstand ein visuell sauberes, geometrisch eindeutiges Zentrum, dessen Leuchtwirkung ausschließlich vom eigentlichen Anzeigeelement ausgeht. Gerade diese Konsequenz dokumentiert, dass gestalterische Entscheidungen im Projekt nicht zufällig, sondern analytisch begründet getroffen wurden.

### 3.13 Konsolidierung des aktuellen Entwicklungsstands
Der aktuelle Projektstand lässt sich insgesamt als Phase der Konsolidierung beschreiben. Kennzeichnend hierfür sind:

- modularisierte Logik
- strukturierte Bereitstellung der Daten durch das Backend
- verarbeitungsfähige Frontend-Mechanismen für Live-Daten, Szenario-Override und externe Kontextquellen
- deutlich verbesserte Erklärbarkeit systemischer Entscheidungen

Damit hat sich das Projekt von einer grundlegenden Funktionsidee zu einem präsentationsreifen Prototyp entwickelt, der sowohl technisch als auch gestalterisch eine erkennbare innere Geschlossenheit aufweist.

## 4. Systemlogik

### 4.1 Berechnung des Risk Index
Der Risk Index stellt die zentrale Kennzahl des Systems dar. In der Python-Kernlogik wird er über eine gewichtete Formel berechnet:

`Risk = Stress*0.45 + (100-Energy)*0.35 + (100-Focus)*0.20 + Ablenkung + Zufall`

Die Entscheidung für eine gewichtete Summenlogik wurde bewusst getroffen. Sie ist transparent, mathematisch gut nachvollziehbar und für den Charakter eines Prototyps fachlich angemessen. Zugleich ermöglicht sie eine differenzierte Berücksichtigung der einzelnen Einflussfaktoren, ohne die Berechnungslogik unnötig intransparenter zu machen.

Im Interface wird diese Kennzahl durch ein zentrales Radialmeter visualisiert, das die numerische Risikobewertung in eine unmittelbar erfassbare grafische Form überführt. Die Verknüpfung von Logik und Darstellung kann im Text über `vgl. Abbildung 3` nachvollzogen werden.

**[Abbildung 3 hier einfügen: Visualisierung des Risk Index im zentralen Radialmeter]**

### 4.2 Einflussfaktoren und ihre Begründung
In die Risikobewertung fließen mehrere Faktoren ein, deren Auswahl und Gewichtung jeweils inhaltlich begründet sind:

- `Stress`
  Hoher Stress wirkt als unmittelbarer Risikotreiber, da er kognitive Überlastung, reduzierte Handlungssicherheit und unruhige Fahrreaktionen begünstigt.

- `Energy`
  Sinkende Energie ist ein zentraler Indikator für Ermüdung und damit für verlangsamte Reaktionen sowie verringerte Wachheit.

- `Focus`
  Ein niedriger Fokuswert verweist auf eine reduzierte Aufmerksamkeitsbindung und stellt daher einen relevanten Sicherheitsindikator dar.

- `Ablenkung`
  Ablenkung wurde bewusst als eigener Modifikator sichtbar gemacht, um den Übergang von reinem Fokusverlust zu konkreter Gefährdung explizit markieren zu können.

- `Zufallsoffset`
  Der kleine Offset führt zu einer begrenzten Varianz der Simulation und verhindert, dass das System bei identischen Bedingungen vollkommen deterministisch wirkt. Für einen Demonstrator ist dies zulässig, da dadurch situative Lebendigkeit erzeugt wird, ohne die Grundlogik aufzuheben.

### 4.3 Kontextlogik
Neben der eigentlichen Formel wirkt auch der Kontext auf das System ein. Dabei ist zwischen zwei Ebenen zu unterscheiden:

- In der Telemetrieerzeugung beeinflussen `Tageszeit`, `Fahrkontext`, `Wetter` und `Außentemperatur` direkt die Werte für Stress, Energie und Fokus.
- In der ausgabeseitigen Erklärlogik werden dieselben Faktoren textlich und visuell als Risikotreiber ausgegeben.

Hierdurch entsteht kein abstrakter Einzelwert, sondern ein interpretierbarer Ursache-Wirkungs-Zusammenhang, der sowohl systemisch als auch kommunikativ anschlussfähig ist.

### 4.4 Ableitung von Warnstufen und Fahrmodi
Aus dem Risk Index wird zunächst ein Fahrerzustand abgeleitet:

- ab `65` -> `kritisch`
- ab `35` -> `müde`
- darunter -> `wachsam`

Auf dieser Grundlage entstehen Warnstufe, Assistenzreaktion und Fahrmodus. In der Web-HMI wird diese interne Logik in eine reduzierte Modi-Struktur überführt:

- niedriger Risk Index -> `Komfort`
- mittlerer Risk Index -> `Adaptiv`
- hoher Risk Index -> `Warnmodus`

Parallel dazu existiert im Backend eine feinere fachliche Bewertung mit Assistenzprofilen wie `Wachsamkeit`, `Stabilisierung` oder `Schutzmodus`. Diese Zweiteilung ist konzeptionell sinnvoll, weil sie interne Differenzierungsfähigkeit mit externer Klarheit verbindet.

Die Übersetzung dieser Logik in sichtbare Interface-Elemente wird insbesondere im Zusammenspiel von Risk-Meter, Modusanzeige und Entscheidungskette deutlich; für die dokumentierende Darstellung sind daher insbesondere `Abbildung 2`, `Abbildung 3` und `Abbildung 5` einschlägig.

## 5. UI- und HMI-Design

### 5.1 Gestaltungsprinzipien
Die HMI folgt drei leitenden Gestaltungsprinzipien:

- `Cockpit-Charakter`
  Die Oberfläche orientiert sich an einem technisch präzisen, futuristischen Fahrzeuginterieur.

- `Klarheit`
  Trotz hoher Informationsdichte bleibt die Darstellung hierarchisch gegliedert und funktional strukturiert.

- `Fokus`
  Das visuelle Zentrum bildet der Risk Index innerhalb der Fahreranalyse; alle weiteren Elemente dienen seiner Einordnung und Erklärung.

Diese Prinzipien wurden bewusst priorisiert, um eine hochwertige Cockpit-Anmutung zu erzeugen, ohne die Nutzbarkeit zugunsten rein dekorativer Effekte zu beeinträchtigen.

### 5.2 Visuelle Darstellung der Zustände
Die visuelle Sprache der HMI arbeitet mit mehreren komplementären Ebenen:

- Farbcodierung für Warn- und Risikozustände
- kreisförmiger Radialmeter als zentrales Leitobjekt
- Chips, Badges und Tags für Kontext- und Statusinformationen
- textliche Entscheidungsketten zur Erhöhung der Erklärbarkeit

Von besonderer Bedeutung ist die Kombination aus numerischer und sprachlicher Darstellung. Ein isolierter Prozentwert wäre für sich genommen zu abstrakt. Erst im Zusammenspiel mit Benennung, Warnstufe und begründender Textstruktur entsteht eine Darstellung, die sowohl informativ als auch interpretierbar ist.

Ergänzend dazu machen die linearen Metrikbalken für Stress, Energy und Focus die interne Zustandsstruktur des Systems in kompakter Form sichtbar; diese Ebene der Darstellung kann im Text über `vgl. Abbildung 4` referenziert werden.

**[Abbildung 4 hier einfügen: Darstellung der Zustandsgrößen Stress, Energy und Focus]**

### 5.3 Begründung der reduzierten Effektnutzung
Im Entwicklungsverlauf wurde deutlich, dass eine zu starke Überlagerung durch Glow-, Shadow- und Overlay-Effekte die Lesbarkeit und die wahrgenommene Hochwertigkeit des Interfaces beeinträchtigen kann. Die gestalterische Konsequenz bestand daher nicht in der Maximierung visueller Effekte, sondern in deren gezielter, funktional begründeter Reduktion.

Die Entfernung des quadratischen Glow-Hintergrunds hinter dem Risk-Meter ist hierfür das deutlichste Beispiel. Die Entscheidung für ein sauberes, geometrisch eindeutiges, rundes Design war funktional motiviert:

- Das zentrale Anzeigeelement sollte in seiner Form eindeutig bleiben.
- Störende Hintergrundflächen hätten die visuelle Präzision reduziert.
- Die Leuchtwirkung sollte aus dem Zustand selbst hervorgehen und nicht aus unkontrollierten Nebeneffekten resultieren.

Die Reduktion gestalterischer Überlagerungen war somit kein Verzicht auf Qualität, sondern deren Voraussetzung.

## 6. Technische Umsetzung

### 6.1 Verwendete Technologien
Der Prototyp basiert auf einer für Demonstrationssysteme zweckmäßigen Technologiekombination:

- `HTML` für die semantische Struktur der Web-HMI
- `CSS` für Layout, Farbkonzept, Animation und visuelle Zustandsdarstellung
- `JavaScript` für Datenverarbeitung, UI-Aktualisierung, Szenario-Override und Interaktion
- `Python` für Backend, Risikologik, Datenbereitstellung und vorbereitete externe Kontextanbindung

### 6.2 Systemstruktur
Die aktuelle Struktur des Systems lässt sich in vier zentrale Bereiche gliedern:

- `logic.py`
  Kernmodul der Zustands- und Risikoberechnung

- `main.py`
  HTTP-Server sowie Backend-Aufbereitung der Dashboard-Daten

- `index.html`, `style.css`, `script.js`
  webbasierte HMI mit Simulation, Visualisierung und Erklärlogik

- `ui.py`
  frühere beziehungsweise parallele Desktop-Oberfläche als Zwischenschritt der Visualisierung

Die Systemstruktur kann ergänzend tabellarisch im Anhang aufbereitet und im Haupttext über einen Verweis wie `siehe Anhang D` ergänzt werden.

### 6.3 Trennung von Logik und Darstellung
Ein wesentlicher Qualitätsaspekt des Projekts liegt in der erkennbaren Trennung von Fachlogik und Darstellung:

- Die Python-Seite erzeugt strukturierte Zustandsdaten.
- Das Frontend visualisiert diese Daten in einer klar gegliederten HMI.
- Die Darstellung kann dadurch weiterentwickelt werden, ohne die Kernlogik grundlegend neu formulieren zu müssen.

Gleichzeitig zeigt das Projekt eine typische Herausforderung prototypischer Systeme: Teile der Logik werden im Frontend erneut verarbeitet oder im Rahmen von Simulationen rekonstruiert. Für einen Prototyp ist dies vertretbar, langfristig wäre jedoch eine stärkere Zentralisierung der Entscheidungslogik anzustreben, um Redundanzen zu reduzieren und Konsistenz zu sichern.

## 7. Herausforderungen und Lösungsansätze

### 7.1 Visueller Fehler im zentralen Risk-Meter
Das markanteste konkrete Problem bestand im quadratischen Glow-Effekt hinter dem kreisförmigen Risk-Meter. Die Schwierigkeit lag darin, dass der Fehler nicht im sichtbaren Kernelement selbst, sondern in indirekten CSS-Ebenen der umgebenden Komponenten entstand.

Die Lösung umfasste:

- Analyse der Rendering-Schichten
- Entfernung störender Hintergrundebenen
- Deaktivierung von Pseudo-Elementen
- Reduktion von Box-Shadows, Filtern und Backdrop-Filtern

Das Problem wurde somit nicht oberflächlich kaschiert, sondern ursachenorientiert gelöst. Gerade diese Form systematischer Fehleranalyse ist für die Qualität des Entwicklungsprozesses von besonderer Aussagekraft.

### 7.2 Balance zwischen Informationsdichte und Klarheit
Das System verarbeitet mehrere Faktoren und führt diese in unterschiedlichen Bewertungsebenen zusammen. Daraus ergab sich die Herausforderung, fachliche Tiefe mit unmittelbarer Lesbarkeit zu verbinden.

Gelöst wurde dies durch:

- eine klar gegliederte Panel-Struktur
- die zentrale Hervorhebung des Risk Index
- reduzierte, eindeutig benannte Statusbausteine
- eine textliche Erklärung über Ursache, Analyse, Entscheidung und Aktion

### 7.3 Erweiterung des Systems bei gleichzeitiger Wahrung der Nachvollziehbarkeit
Mit jedem neu integrierten Faktor steigt die Gefahr, dass ein System in seiner Aussage beliebig oder schwer nachvollziehbar wird. Diese Problematik zeigte sich insbesondere bei der Einführung von Wetter, Temperatur, Nachtkontext und Ablenkung.

Die Antwort auf diese Herausforderung bestand in einer bewussten Modularisierung:

- Telemetrieerzeugung
- Risikoformel
- textliche Risikoerklärung
- Fahrmodusableitung
- HMI-Darstellung

Dadurch blieb das System trotz wachsender Komplexität argumentativ geschlossen und nachvollziehbar.

### 7.4 Teamdynamik und Abstimmung
Auch in neutraler Form lässt sich festhalten, dass ein Projekt dieser Art unterschiedliche Anforderungen zusammenführt. Logik, Gestaltung und Präsentation müssen nicht nur parallel entwickelt, sondern in ihren Prioritäten aufeinander abgestimmt werden. Typische Spannungsfelder betreffen dabei weniger die Grundidee als vielmehr die Gewichtung der Entwicklungsschwerpunkte:

- Soll die Logik weiter ausdifferenziert werden oder die HMI zunächst vereinfacht werden?
- Wie stark darf die Visualisierung emotionalisiert sein, ohne an funktionaler Klarheit zu verlieren?
- Welche Informationen sind für die Cockpit-Kommunikation erforderlich und welche eher technisch-intern relevant?

Die neutrale Schlussfolgerung lautet, dass Fortschritt insbesondere dort erreicht wurde, wo Entscheidungen klar priorisiert und anschließend konsequent umgesetzt wurden.

### 7.5 Systematische Problemlösung als Entwicklungsprinzip
Über den gesamten Verlauf hinweg lässt sich ein wiederkehrendes Muster erkennen: Probleme wurden nicht isoliert überdeckt, sondern schrittweise analysiert, eingegrenzt und lösungsorientiert bearbeitet. Dieses Vorgehen zeigte sich sowohl bei der Risikologik als auch bei der visuellen Fehlerbehebung und bei der Integration neuer Faktoren.

Für die Bewertung des Projekts ist dies deshalb bedeutsam, weil hieran erkennbar wird, dass die Entwicklung nicht nur iterativ, sondern auch methodisch reflektiert erfolgte.

## 8. Ergebnis und aktueller Stand

### 8.1 Funktionsumfang
Der aktuelle Prototyp weist einen klar präsentierbaren Entwicklungsstand auf. Gegenwärtig funktionsfähig sind insbesondere:

- Analyse von Stress, Energy und Focus
- Ableitung eines Ablenkungsstatus
- Berechnung und Ausgabe eines Risk Index
- Ableitung von Warnstufen und Fahrmodi
- webbasierte HMI mit Dashboard-Struktur und zentralem Risk-Meter
- Szenario-Override für Zeit, Kontext und Wetter
- vorbereitete externe Kontextintegration über Home Assistant
- textliche Erklärung von Ursachen, Analyse, Entscheidung und Aktion

Die Breite dieses Funktionsumfangs wird in der Oberfläche insbesondere durch das Zusammenspiel aus Kontextpanel, Telemetriedarstellung, Assistenzreaktion, Entscheidungskette und Szenario-Override sichtbar; dies lässt sich vor allem über `Abbildung 2`, `Abbildung 6`, `Abbildung 7` und `Abbildung 8` dokumentieren.

**[Abbildung 6 hier einfügen: Kontextpanel mit Route, Wetter, Verkehr und Tageszeit]**

**[Abbildung 7 hier einfügen: Szenario-Override zur Variation von Uhrzeit, Fahrkontext und Wetter]**

**[Abbildung 8 hier einfügen: Einbindung externer Kontextinformationen über Home Assistant]**

### 8.2 Stabile Komponenten
Als stabil können derzeit insbesondere folgende Komponenten eingeordnet werden:

- die Kernlogik der Zustandsanalyse
- die datenbasierte Aufbereitung im Backend
- die visuelle Grundstruktur der Web-HMI
- die farbliche und begriffliche Zuordnung von Risikoniveaus

### 8.3 Bewertung des Prototyps
Der Prototyp ist im aktuellen Stand als hochwertiger Demonstrator einzuordnen. Besonders hervorzuheben sind:

- die nachvollziehbare Regelbasis
- die erkennbare Entwicklung von einer funktionalen Grundlogik zu einem präsentationsreifen Frontend
- die bewusste Verbindung von Analyse, Systementscheidung und HMI

Damit liegt nicht lediglich eine technische Machbarkeitsstudie vor, sondern ein argumentativ tragfähiges Konzept für fahrerzustandsbasierte Assistenz im Cockpitkontext.

## 9. Reflexion und Weiterentwicklung

### 9.1 Positive Aspekte des Entwicklungsverlaufs
Besonders gelungen ist die klare Entwicklungslinie des Projekts. Das System wurde nicht von Beginn an mit maximaler Komplexität versehen, sondern schrittweise erweitert. Dadurch blieb jede Erweiterung begründbar und konnte in die bestehende Gesamtlogik integriert werden.

Positiv hervorzuheben sind insbesondere:

- die frühe Konzentration auf wenige, aber aussagekräftige Kernparameter
- die spätere Ergänzung von Ablenkung als sinnvoller neuer Einflussgröße
- die deutliche Aufwertung der HMI im Zuge der webbasierten Umsetzung
- die konsequente Beseitigung visueller Störfaktoren

### 9.2 Verbesserungsmöglichkeiten
Aus technischer Perspektive wäre als nächster Schritt vor allem eine weitergehende Vereinheitlichung der Entscheidungslogik sinnvoll. Gegenwärtig bestehen parallele Bewertungsebenen in Python und JavaScript. Für einen Prototyp ist dies akzeptabel, langfristig wäre jedoch eine stärker zentralisierte Logik robuster und wartungsfreundlicher.

Darüber hinaus erscheinen folgende Weiterentwicklungen sinnvoll:

- formale Validierung der Gewichtungen im Risk Index
- systematische Testfälle für Grenzwerte und Sonderkonstellationen
- deutlichere Trennung zwischen demonstrativer Varianz und fachlicher Bewertung
- Anbindung realer statt vorbereiteter externer Datenquellen

### 9.3 Sinnvolle nächste Schritte
Für die weitere Entwicklung bieten sich insbesondere folgende Schritte an:

1. Vereinheitlichung der Entscheidungslogik in einer zentralen Quelle
2. Ausbau der Schnittstellen zu realen Sensor- oder Kontextdaten
3. Ergänzung formaler Tests für Risiko- und Modusgrenzen
4. Feinschliff der HMI für mobile oder eingebettete Darstellungsformate
5. Erweiterung um dokumentierte Nutzungsszenarien und Vergleichsfälle

## 10. Fazit

Das Porsche Cockpit Intelligence System zeigt, wie ein fahrerzustandsbasiertes Assistenzkonzept technisch, gestalterisch und argumentativ kohärent ausgearbeitet werden kann. Die besondere Stärke des Projekts liegt nicht allein in der Visualisierung eines futuristischen Cockpits, sondern in der bewussten Verknüpfung von Zustandsanalyse, Risikobewertung und systemischer Reaktion.

Für eine akademische Projektdokumentation ist entscheidend, dass Entwicklung nicht lediglich als Ergebnis, sondern als begründeter Entstehungsprozess sichtbar wird. Genau hierin liegt die besondere Qualität des Projekts: Entscheidungen wurden nicht zufällig getroffen, sondern schrittweise hergeleitet, überprüft, angepasst und in eine nachvollziehbare Gesamtlogik überführt. In dieser Form besitzt der Prototyp sowohl technischen als auch konzeptionellen Wert und stellt eine belastbare Grundlage für weiterführende Entwicklungen dar.

---

**Seitenumbruch für Word einfügen**

---

## 11. Literatur- und Quellenverzeichnis

Da es sich bei der vorliegenden Arbeit primär um eine Projektdokumentation eines eigenständig entwickelten Prototyps handelt, beziehen sich die zentralen Aussagen im Wesentlichen auf die eigene Konzeption, Implementierung und Auswertung des Systems.

### 11.1 Verwendete Projektartefakte

- `logic.py`
- `main.py`
- `script.js`
- `style.css`
- `index.html`
- `ui.py`
- `home_assistant.py`
- `state.py`

### 11.2 Formal nutzbares Quellenraster im APA-Stil

Die folgenden Muster können direkt durch reale Literatur ersetzt oder ergänzt werden:

1. Nachname, N. N. (Jahr). *Titel des Buches*. Verlag.
2. Nachname, N. N. (Jahr). Titel des Aufsatzes. *Titel der Zeitschrift*, Band(Ausgabe), Seitenbereich.
3. Institution. (Jahr). *Titel des Dokuments*. URL
4. Eigene Projektartefakte. (2026). *Porsche Cockpit Intelligence System: Quellcode und Interface-Implementierung*.

### 11.3 Optional sinnvolle wissenschaftliche Quellenkategorien

- Literatur zu Fahrerzustandsanalyse
- Literatur zu Human-Machine Interface Design im Fahrzeug
- Literatur zu erklärbarer Systemlogik
- Literatur zu Risikomodellierung und Entscheidungsunterstützung

---

**Seitenumbruch für Word einfügen**

---

## 12. Abbildungsverzeichnis

Die folgenden Einträge sind bereits auf den tatsächlichen Aufbau des Prototyps abgestimmt und können in Word direkt mit eingefügten Screenshots verknüpft werden:

- **Abbildung 1:** Frühere Desktop-Oberfläche als Zwischenstand der visuellen Konzeptentwicklung  
  *Eigene Darstellung auf Basis der Python-basierten Desktop-Implementierung.*

- **Abbildung 2:** Gesamtansicht der webbasierten Cockpit-Oberfläche des Porsche Cockpit Intelligence System  
  *Eigene Darstellung des finalen Web-Interfaces mit Dashboard-Struktur.*

- **Abbildung 3:** Darstellung des zentralen Risk Index im Radialmeter innerhalb des Driver-State-Panels  
  *Eigene Darstellung der visuellen Verdichtung der Risikologik.*

- **Abbildung 4:** Visualisierung der Zustandsgrößen Stress, Energy und Focus in Form linearer Metrikbalken  
  *Eigene Darstellung der drei zentralen Zustandsvariablen des Systems.*

- **Abbildung 5:** Entscheidungskette mit Input, Analyse, Entscheidung und Aktion  
  *Eigene Darstellung der erklärbaren Ableitung systemischer Reaktionen.*

- **Abbildung 6:** Darstellung der Kontextinformationen einschließlich Wetter, Route, Verkehr und Tageszeit  
  *Eigene Darstellung der kontextbezogenen Einflussgrößen innerhalb der HMI.*

- **Abbildung 7:** Szenario-Override zur Variation von Uhrzeit, Fahrkontext und Wetter  
  *Eigene Darstellung der interaktiven Simulationssteuerung.*

- **Abbildung 8:** Einbindung externer Kontextinformationen über die vorbereitete Home-Assistant-Schnittstelle  
  *Eigene Darstellung der erweiterten Kontextintegration.*

- **Abbildung 9:** 3D-State-Scan zur visualisierten Interpretation des Fahrerzustands  
  *Eigene Darstellung des ergänzenden Scan-Overlays zur Zustandsinterpretation.*

- **Abbildung 10:** Vergleich des Radialmeters vor und nach der visuellen Bereinigung des quadratischen Glow-Effekts  
  *Eigene Gegenüberstellung zur Dokumentation des UI-Bugs und seiner Behebung.*

**Hinweis zur formalen Ausgestaltung:**  
Jede Abbildung sollte unterhalb des Bildes mit einer standardisierten Beschriftung versehen werden, beispielsweise:  
`Abbildung 1: Gesamtansicht der webbasierten Cockpit-Oberfläche. Eigene Darstellung.`

---

**Seitenumbruch für Word einfügen**

---

## 13. Anhang

Der Anhang sollte in der finalen Abgabe ergänzende Materialien enthalten, die für das Verständnis oder die Nachvollziehbarkeit des Projekts relevant sind, jedoch den Lesefluss im Hauptteil unterbrechen würden.

### 13.1 Empfohlene Struktur des Anhangs

- **Anhang A:** Screenshots zentraler Entwicklungsstände
- **Anhang B:** Auszüge aus der Risikologik
- **Anhang C:** Übersicht der Zustands- und Fahrmodi
- **Anhang D:** Technische Zusatzinformationen zur Systemstruktur
- **Anhang E:** Beispielszenarien für Simulation und Bewertung

### 13.2 Konkrete Anhangsinhalte

- Abbildungen der frühen Desktop-Oberfläche
- Abbildungen der finalen Web-HMI
- Ausschnitte aus `logic.py` zur Berechnung des Risk Index
- Darstellung der Ablenkungslogik
- Übersicht über Fahrmodi, Warnstufen und Systemreaktionen
- Dokumentation des quadratischen Glow-Bugs und seiner Behebung

### 13.3 Formulierungsvorschlag für Verweise im Haupttext

Im Fließtext können Verweise wie die folgenden verwendet werden:

- `vgl. Anhang A, Abbildung 3`
- `siehe Anhang B`
- `eine Detaildarstellung der Risikologik befindet sich in Anhang B`

### 13.4 Formulierungsvorschläge für Abbildungsunterschriften im Fließtextstil

Die folgenden Formulierungen können in Word direkt unter eingefügten Screenshots verwendet werden:

- `Abbildung 1: Frühere Desktop-Oberfläche des Systems als Zwischenstand der visuellen Entwicklung. Eigene Darstellung.`
- `Abbildung 2: Gesamtansicht der webbasierten Cockpit-Oberfläche mit Dashboard-Struktur. Eigene Darstellung.`
- `Abbildung 3: Visualisierung des Risk Index im zentralen Radialmeter. Eigene Darstellung.`
- `Abbildung 4: Darstellung der Zustandsgrößen Stress, Energy und Focus. Eigene Darstellung.`
- `Abbildung 5: Entscheidungskette aus Input, Analyse, Entscheidung und Aktion. Eigene Darstellung.`
- `Abbildung 6: Kontextpanel mit Route, Wetter, Verkehr und Tageszeit. Eigene Darstellung.`
- `Abbildung 7: Szenario-Override zur Variation situativer Eingabeparameter. Eigene Darstellung.`
- `Abbildung 8: Einbindung externer Kontextinformationen über Home Assistant. Eigene Darstellung.`
- `Abbildung 9: 3D-State-Scan zur ergänzenden Interpretation des Fahrerzustands. Eigene Darstellung.`
- `Abbildung 10: Vergleich des Radialmeters vor und nach der Korrektur des quadratischen Glow-Effekts. Eigene Darstellung.`

---

## Abschließender Hinweis zur Finalisierung

Vor der endgültigen Abgabe sollten noch folgende Punkte ergänzt oder angepasst werden:

- persönliche Angaben auf dem Deckblatt
- automatische Verzeichnisse in Word
- echte Seitenzahlen
- tatsächlich eingefügte Screenshots
- gegebenenfalls reale Literaturquellen im gewünschten Zitierstil
- letzte formale Prüfung auf Vorgaben der Hochschule oder des Moduls
