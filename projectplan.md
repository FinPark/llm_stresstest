# LLM Stresstest - Projektplan

## Projektziel
Entwicklung einer robusten Test-Anwendung f�r Large Language Models (LLMs) zur Bewertung von Performance und Hardware-Anforderungen mit vergleichbaren und analysierbaren Ergebnissen.

## Architektur

### Hauptkomponenten

1. **Konfigurationsmanagement**
   - Laden von `config.json` mit Testparametern
   - Validierung der Konfiguration
   - Fehlerbehandlung bei fehlenden/falschen Werten

2. **Fragenmanagement**
   - Laden der Fragen aus `questions.json`
   - Sequenzielle Auswahl basierend auf `questions` Parameter
   - Unterst�tzung f�r parallele Anfragen (`concurrent`)

3. **LLM-Kommunikation**
   - OpenAI-kompatible API Anbindung
   - Asynchrone Anfragen mit aiohttp
   - Timeout-Handling
   - Connection Pooling f�r Performance

4. **Ergebnisverarbeitung**
   - Strukturierte JSON-Ausgabe im `results/` Ordner
   - Zeitstempel und Metadaten
   - Einzelergebnisse pro Frage
   - Aggregierte Statistiken

5. **Fehlerbehandlung & Logging**
   - Detailliertes Error-Logging
   - Graceful Degradation - kein Absturz
   - Logging in separate Datei
   - Verschiedene Log-Level (DEBUG, INFO, WARNING, ERROR)

## Datenstrukturen

### Input
- **config.json**: Testkonfiguration
- **questions.json**: Fragenkatalog
- **CLI-Parameter**: Ausgabedateiname

### Output (results/*.json)
```json
{
  "meta": {
    "start_date": "YYYY-MM-DD",
    "start_time": "HH:MM:SS.mmm",
    "end_date": "YYYY-MM-DD",
    "end_time": "HH:MM:SS.mmm",
    "server": "url aus config",
    "model": "model aus config",
    "concurrent": "concurrent aus config",
    "questions": "questions aus config",
    "timeout": "timeout aus config",
    "total_duration_ms": "berechnet"
  },
  "results": [
    {
      "question": "Frage aus questions.json",
      "answer": "Antwort vom LLM",
      "time": "Response Zeit in ms",
      "token": "Anzahl generierter Tokens",
      "quality": "Gesamtqualit�tsbewertung (0-10)",
      "quality_metrics": {
        "structure": "Struktur-Bewertung (0-10)",
        "readability": "Lesbarkeits-Bewertung (0-10)",
        "completeness": "Vollst�ndigkeits-Bewertung (0-10)",
        "relevance": "Relevanz-Bewertung (0-10)",
        "factual_consistency": "Faktische Konsistenz (0-10)",
        "language_flow": "Sprachfluss-Bewertung (0-10)",
        "coherence": "Koh�renz-Bewertung (0-10)",
        "overall_quality": "Gesamtqualit�t (0-10)"
      }
    }
  ],
  "aggregate": {
    "runtime_sum": "Summe aller Zeiten",
    "runtime_avg": "Durchschnitt",
    "runtime_min": "Minimum",
    "runtime_max": "Maximum",
    "token_sum": "Summe aller Tokens",
    "token_avg": "Durchschnitt",
    "token_min": "Minimum",
    "token_max": "Maximum",
    "quality_sum": "Summe aller Quality-Scores",
    "quality_avg": "Durchschnittliche Qualit�t",
    "quality_min": "Minimale Qualit�t",
    "quality_max": "Maximale Qualit�t"
  }
}
```

## Implementierungsschritte

1. **Setup & Dependencies**
   - uv add openai (f�r OpenAI-kompatible API)
   - uv add aiohttp (f�r async HTTP)
   - uv add asyncio (f�r concurrent requests)
   - Logging-Konfiguration

2. **Core-Funktionen**
   - `load_config()`: Config laden und validieren
   - `load_questions()`: Fragen laden
   - `test_connection()`: Verbindung pr�fen
   - `send_question()`: Einzelne Frage senden
   - `process_questions()`: Batch-Verarbeitung
   - `calculate_aggregates()`: Statistiken berechnen
   - `save_results()`: Ergebnisse speichern

3. **Error Handling**
   - Connection Errors
   - Timeout Errors
   - API Errors
   - File I/O Errors
   - JSON Parse Errors

4. **CLI Interface**
   ```bash
   python llm_stresstest.py <output_filename>
   # Beispiel: python llm_stresstest.py results_PC_FIN_qwen13b
   ```

## Robustheit-Ma�nahmen

1. **Fehlertoleranz**
   - Try-catch f�r alle kritischen Operationen
   - Fallback-Werte bei Fehlern
   - Fortsetzung bei einzelnen fehlgeschlagenen Anfragen

2. **Logging**
   - Strukturiertes Logging mit Zeitstempeln
   - Separate Log-Datei pro Run
   - Error-Stack-Traces f�r Debugging

3. **Validierung**
   - Input-Validierung f�r Config und Questions
   - Type-Checking f�r API-Responses
   - Pfad-Validierung f�r Output-Dateien

4. **Performance**
   - Async/Await f�r parallele Anfragen
   - Connection Pooling
   - Timeout-Management

## Testing-Strategie

1. **Unit Tests**
   - Config-Loading
   - Question-Loading
   - Aggregation-Funktionen

2. **Integration Tests**
   - API-Kommunikation
   - File I/O
   - End-to-End Workflow

3. **Error Tests**
   - Verbindungsfehler
   - Timeout-Szenarien
   - Falsche Konfiguration

## Erweiterungen - Umgesetzt

### Qualit�tsbewertung der Antworten ✅ IMPLEMENTIERT
- **Quality Evaluator** vollst�ndig in `llm_stresstest.py` integriert
- 8 Qualit�tsmetriken: Struktur, Lesbarkeit, Vollst�ndigkeit, Relevanz, faktische Konsistenz, Sprachfluss, Koh�renz, Gesamtqualit�t
- 4 zus�tzliche Kennzahlen: Wortanzahl, Satzanzahl, durchschnittliche Satzl�nge, Wiederholungsrate
- Automatische Bewertung bei jeder LLM-Antwort
- Quality-Aggregation in Statistiken (sum, avg, min, max)
- Erweiterte JSON-Struktur mit `quality` und `quality_metrics` Feldern

### Architektur-�nderungen
- Quality Evaluator als integrierte Klasse statt separates Modul
- Neue Abh�ngigkeiten (optional): spacy, sentence-transformers
- Erweiterte Datenstrukturen f�r Qualit�tsmetriken
- Robuste Fehlerbehandlung bei Quality-Bewertung (Fallback auf 0.0)

### Dashboard & Auswertung ✅ IMPLEMENTIERT
- **Streamlit Dashboard** (`llm_auswertung.py`) vollständig implementiert
- **5 Hauptbereiche**:
  - 📊 Übersicht: Gesamtstatistiken und Tabellenansicht aller Tests
  - 📝 Log-Analyse: Durchsuchen und Filtern von Logs mit automatischer Fehleranzeige
  - ⚡ Performance: Token/Zeit-Analyse, Performance-Rankings, Effizienz-Matrix
  - 🔄 Vergleiche: Server- und Modell-Vergleiche mit interaktiven Grafiken
  - 📈 Qualitätsmetriken: Radar-Charts, Box-Plots, detaillierte Statistiken
- **Dark Mode Support** mit umfangreichen CSS-Optimierungen
- **Cross-Platform** Unterstützung (Windows, macOS, Linux)
- **Interaktive Visualisierungen** mit Plotly
- **CSV-Export** Funktionalität
- **Live-Log-Monitoring** mit Fehler- und Warnungshervorhebung

### LLM Load Time Measurement ✅ IMPLEMENTIERT
- **Warmup-Phase** zur Messung der LLM-Ladezeit
- **Cold Start Factor** Berechnung (Ladezeit/Durchschnittszeit)
- **Präzise Zeitmessung** durch doppelte Ausführung der ersten Frage
- **Erweiterte Metriken** in JSON-Output (`llm_load_time`, `cold_start_factor`)

### Server Naming ✅ IMPLEMENTIERT
- **server_name** Konfigurationsfeld für sprechende Server-Bezeichnungen
- **Fallback-Mechanismus** auf URL wenn kein Name gesetzt
- **Dashboard-Integration** mit korrekter Anzeige der Server-Namen

### UI/UX Verbesserungen ✅ IMPLEMENTIERT
- **Kontrastprobleme behoben**: Log-Anzeige mit hellem Hintergrund für bessere Lesbarkeit
- **Navigation optimiert**: Sidebar-Buttons mit korrekten Hover-Effekten in Light/Dark Mode
- **Elegante Animationen**: Smooth Transitions und Schatten-Effekte
- **Responsive Design**: Optimiert für verschiedene Bildschirmgrößen

### Vergleichbarkeits-Features ✅ IMPLEMENTIERT
- **Normalisierte Metriken** in get_dataframe() für faire Vergleiche:
  - `concurrent_efficiency`: Performance pro Thread (Performance ÷ concurrent)
  - `throughput_per_min`: Fragen pro Minute basierend auf durchschnittlicher Antwortzeit
  - `load_efficiency`: Anteil Netto-Inferenzzeit in Prozent (ohne LLM-Ladezeit)
  - `performance_normalized` und `quality_normalized`: Bestehende Metriken beibehalten
- **Erweiterte Übersichtsseite**:
  - Vergleichbarkeits-Hinweis bei unterschiedlichen Konfigurationen
  - Tabelle mit `concurrent` und `throughput_per_min` Spalten
  - Fix für numpy.int64 Darstellung in Listen
- **Performance-Bereich überarbeitet**:
  - Info-Box über normalisierte Metriken
  - Neue Metrik-Tiles für alle normalisierten Werte
  - Scatter-Plot mit erweiterten Hover-Daten
- **Vergleichsbereich aktualisiert**:
  - Hinweis auf normalisierte Metriken in beiden Vergleichsmodi
  - Detailtabellen mit allen relevanten Spalten
  - Multi-Metrik Balkendiagramm nutzt normalisierte Werte
- **Plotly Dependency hinzugefügt** für erweiterte Visualisierungen
- **Faire Vergleiche** zwischen Tests mit unterschiedlichen `questions` und `concurrent` Einstellungen

## Erweiterungsmöglichkeiten - Noch offen

- A/B Testing zwischen verschiedenen Modellen
- Benchmark-Vergleiche mit Standarddatensätzen
- Integration mit CI/CD Pipelines
- REST API für externe Tools
- Automatische Report-Generierung
- E-Mail-Benachrichtigungen bei Tests