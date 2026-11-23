# Hinweise zur automatischen Prüfung

Stand: 23.11.2026. **Eigenprojekt / Demo, kein Kundenauftrag.**

- [`validation-report.txt`](validation-report.txt) ist die Ausgabe von `scripts/validate.py`. Er gilt nur für den Dateistand zum Zeitpunkt seiner Erzeugung (Datum und Anzahl geprüfter Dateien im Kopf). Nach jeder späteren Änderung ist er erneut zu erzeugen.
- Der Bericht wurde mit dem privaten Quell-Export (`--source`) erzeugt: S2b, S4, S6 (Vergleich mit der Quelle) und S7 sind damit ausgeführt. Persönliche Suchbegriffe (`--deny`) sind darin **nicht** verwendet; sie kennt nur der Autor. Vor einer Veröffentlichung muss der Lauf mit `--deny` auf dem endgültigen Dateistand wiederholt werden; der neue Bericht ersetzt den bisherigen.
- Abdeckung: erlaubte Schlüssel (S3), Muster in allen Dateien (S5: E-Mail-Adressen ausser example.com, Links ausserhalb der Liste, Nummern ab 7 Ziffern, Schlüssel und Tokens, IPv4, n8n-IDs mit 16 Zeichen), Struktur (S6: 27 Nodes, 28 Verbindungen, Verweise auf Nodes), nur genehmigte Änderungen gegenüber der Quelle (S7), Flags (S8), Kalender `primary` und genau ein Platzhalter für die Benutzer-ID (S9), synthetische Testdaten (S10).
- Automatische Prüfungen sind **kein Beweis**, dass keine sensiblen Daten mehr enthalten sind; eine manuelle Durchsicht war Teil der Bereinigung.

## Wirksamkeit der Prüfung

`validate.py` wurde an acht absichtlich veränderten Kopien des Repositorys getestet; jede Veränderung wird erkannt (FAIL): fremde E-Mail-Adresse in einer Datei, Zugangsdaten an einem Node, Kalender-Adresse in der URL, nicht genehmigte Änderung am Code-Node, eine Kennung aus der Quelle (Chat-ID) in einer Datei, API-Schlüssel, Workflow aktiv, Testdaten nicht als synthetisch markiert. Für die Fassung mit Absenderfilter wurden zusätzlich geprüft: die echte Benutzer-ID statt des Platzhalters im Filter und ein fehlender Platzhalter werden erkannt.
