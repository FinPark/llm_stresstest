# LLM Stresstest - Projektplan

## Projektziel
Entwicklung einer robusten Test-Anwendung für Large Language Models (LLMs) zur Bewertung von Performance und Hardware-Anforderungen mit vergleichbaren und analysierbaren Ergebnissen.

## Architektur

### Hauptkomponenten

1. **Konfigurationsmanagement**
   - Laden von `config.json` mit Testparametern
   - Validierung der Konfiguration
   - Fehlerbehandlung bei fehlenden/falschen Werten

2. **Fragenmanagement**
   - Laden der Fragen aus `questions.json`
   - Sequenzielle Auswahl basierend auf `questions` Parameter
   - Unterstützung für parallele Anfragen (`concurrent`)

3. **LLM-Kommunikation**
   - OpenAI-kompatible API Anbindung
   - Asynchrone Anfragen mit aiohttp
   - Timeout-Handling
   - Connection Pooling für Performance

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
      "quality": 0.0
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
    "token_max": "Maximum"
  }
}
```

## Implementierungsschritte

1. **Setup & Dependencies**
   - uv add openai (für OpenAI-kompatible API)
   - uv add aiohttp (für async HTTP)
   - uv add asyncio (für concurrent requests)
   - Logging-Konfiguration

2. **Core-Funktionen**
   - `load_config()`: Config laden und validieren
   - `load_questions()`: Fragen laden
   - `test_connection()`: Verbindung prüfen
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

## Robustheit-Maßnahmen

1. **Fehlertoleranz**
   - Try-catch für alle kritischen Operationen
   - Fallback-Werte bei Fehlern
   - Fortsetzung bei einzelnen fehlgeschlagenen Anfragen

2. **Logging**
   - Strukturiertes Logging mit Zeitstempeln
   - Separate Log-Datei pro Run
   - Error-Stack-Traces für Debugging

3. **Validierung**
   - Input-Validierung für Config und Questions
   - Type-Checking für API-Responses
   - Pfad-Validierung für Output-Dateien

4. **Performance**
   - Async/Await für parallele Anfragen
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

## Erweiterungsmöglichkeiten

- Qualitätsbewertung der Antworten
- Grafische Auswertung der Ergebnisse
- Vergleichstool für mehrere Runs
- Export in verschiedene Formate (CSV, Excel)
- Web-Interface für Monitoring
- Echtzeit-Dashboard