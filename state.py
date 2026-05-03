from dataclasses import dataclass


@dataclass
class Systemzustand:
    kontext: str
    ist_aktiv: bool
    risiko_begruendung: str = ""
    risiko_details: str = ""
