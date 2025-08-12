# LLM Stress Test Tool

Ein robustes Python-Tool zum Testen der Performance und Hardware-Anforderungen von Large Language Models (LLMs).

## Features

- Unterstützt OpenAI-kompatible APIs (Ollama, vLLM, etc.)
- Parallele und sequenzielle Anfrageverarbeitung
- Detaillierte Performance-Metriken (Zeit, Tokens)
- **Automatische Qualitätsbewertung** mit 8 verschiedenen Metriken
- Robuste Fehlerbehandlung ohne Abstürze
- Strukturierte JSON-Ausgabe für Analysen
- Umfassendes Logging-System

## Qualitätsbewertung

Das Tool bewertet automatisch jede LLM-Antwort anhand von 8 Qualitätsmetriken:

- **Struktur**: Logische Gliederung und Organisation der Antwort
- **Lesbarkeit**: Klarheit und Verständlichkeit der Sprache
- **Vollständigkeit**: Wie vollständig die Frage beantwortet wurde
- **Relevanz**: Relevanz der Antwort zur gestellten Frage
- **Faktische Konsistenz**: Korrektheit der Fakten und Informationen
- **Sprachfluss**: Natürlichkeit und Flüssigkeit der Sprache
- **Kohärenz**: Innere Logik und Zusammenhang der Antwort
- **Gesamtqualität**: Übergreifende Bewertung der Antwortqualität

Zusätzlich werden folgende Kennzahlen erfasst:
- Anzahl Wörter
- Anzahl Sätze
- Durchschnittliche Satzlänge
- Wiederholungsrate (häufigste Wörter)

## Installation

```bash
# Repository klonen
git clone <repository-url>
cd llm_stresstest

# Virtual Environment erstellen (einmalig)
uv venv

# Virtual Environment aktivieren (bei jeder Terminal-Session)
source .venv/bin/activate

# Dependencies installieren
uv sync
```

## Konfiguration

Bearbeite `config/config.json`:

```json
{
    "questions": 5,                    // Anzahl der zu testenden Fragen
    "concurrent": 1,                   // Anzahl paralleler Anfragen
    "url": "http://localhost:11434",   // LLM API Endpoint
    "server_name": "MacBook Pro M1",   // Sprechender Server-Name für Auswertungen
    "model": "llama2",                 // Modell-Name
    "timeout": 120.0,                  // Timeout in Sekunden
    "max_keepalive_connections": 20    // Connection Pool Größe
}
```

### Konfigurationsparameter

- **`questions`**: Anzahl der zu testenden Fragen aus dem Fragenkatalog
- **`concurrent`**: Anzahl paralleler Anfragen (1 = sequenziell) 
- **`url`**: LLM API Endpoint (OpenAI-kompatibel)
- **`server_name`**: Sprechender Server-Name für Dashboard-Auswertungen (optional, fallback auf URL)
- **`model`**: Modell-Identifier für den LLM-Server
- **`timeout`**: Request-Timeout in Sekunden
- **`max_keepalive_connections`**: Connection Pool Größe für Performance

## Verwendung

```bash
# Einfach starten - Dateiname wird automatisch generiert
python llm_stresstest.py
```

Der Dateiname wird automatisch aus `server_name` und `model` aus der Konfiguration generiert:
- Format: `result_{server_name}_{model}.json`
- Leerzeichen werden zu `-`, Sonderzeichen zu `_`
- Beispiel: `"MacBook Pro M1"` + `"gemma3:12b"` → `result_MacBook-Pro-M1_gemma3_12b.json`

Die Ergebnisse werden in `results/` gespeichert.

## Ausgabeformat

Die Ergebnis-JSON enthält:

- **meta**: Metadaten zum Testlauf (Zeitstempel, Server, Modell)
- **results**: Einzelergebnisse für jede Frage mit Qualitätsbewertung
- **aggregate**: Aggregierte Statistiken (Durchschnitt, Min, Max) inkl. Quality-Metriken

Beispiel:
```json
{
  "meta": {
    "start_date": "2025-08-11",
    "start_time": "22:12:11.439",
    "server": "http://localhost:11434",
    "model": "llama2",
    "concurrent": 1,
    "questions": 5,
    "timeout": 120.0,
    "total_duration_ms": 23456.7
  },
  "results": [
    {
      "question": "Was ist die Hauptstadt von Deutschland?",
      "answer": "Die Hauptstadt von Deutschland ist Berlin.",
      "time": 1234.5,
      "token": 42,
      "quality": 8.5,
      "quality_metrics": {
        "structure": 9.0,
        "readability": 8.0,
        "completeness": 8.5,
        "relevance": 9.0,
        "factual_consistency": 9.0,
        "language_flow": 8.0,
        "coherence": 8.5,
        "overall_quality": 8.5
      }
    }
  ],
  "aggregate": {
    "runtime_sum": 6172.5,
    "runtime_avg": 1234.5,
    "runtime_min": 1000.0,
    "runtime_max": 1500.0,
    "token_sum": 210,
    "token_avg": 42,
    "token_min": 35,
    "token_max": 50,
    "quality_sum": 42.5,
    "quality_avg": 8.5,
    "quality_min": 7.0,
    "quality_max": 9.2
  }
}
```

## Fragen

Die Fragen werden aus `config/questions.json` geladen. Die Datei enthält 234 vordefinierte Fragen auf Deutsch zu verschiedenen IT- und Technologie-Themen.

## Logging

Log-Dateien werden automatisch mit Zeitstempel erstellt:
- Konsolen-Ausgabe für Live-Monitoring
- Detaillierte Log-Datei: `logs/llm_stresstest_YYYYMMDD_HHMMSS.log`

## Fehlerbehandlung

- Verbindungsfehler führen zum sofortigen Abbruch
- Einzelne fehlgeschlagene Anfragen stoppen nicht den gesamten Test
- Notfall-Speicherung bei Fehlern beim regulären Speichern
- Alle Fehler werden mit Stack-Traces geloggt

## Anforderungen

- Python 3.8+
- uv (für Dependency Management)
- OpenAI-kompatibler LLM-Server

## Optionale Dependencies für erweiterte NLP-Features

```bash
# Für erweiterte Sprachanalyse (optional)
uv add spacy
uv add sentence-transformers

# spaCy Modell herunterladen
python -m spacy download de_core_news_sm
```

## Grafische Auswertung

Das Tool enthält ein umfassendes Streamlit-Dashboard zur Analyse aller Testergebnisse:

```bash
# Dashboard starten
streamlit run llm_auswertung.py

# Oder mit speziellem Port
streamlit run llm_auswertung.py --server.port 8502
```

### Dashboard-Features

- **📊 Übersicht**: 
  - Gesamtstatistiken und Tabellenansicht aller Tests mit Vergleichbarkeits-Hinweisen
  - **Globale Performance-Analyse**: Aggregierte Performance-Metriken pro Modell über alle Server
    - Balkendiagramm mit verbesserter Darstellung (mehrzeilige Labels, Farbkodierung nach Server)
    - Performance-Ranking Tabelle mit Min/Max/Durchschnitt
  - **Globale Qualitäts-Analyse**: Aggregierte Qualitäts-Metriken pro Modell über alle Server
    - Balkendiagramm mit verbesserter Darstellung (mehrzeilige Labels, Farbkodierung nach Server)
    - Qualitäts-Ranking Tabelle
- **📝 Log-Analyse**: Durchsuchen und Filtern von Logs, automatische Fehleranzeige
- **⚡ Performance**: 
  - Token/Zeit-Analyse mit normalisierten Metriken
  - Performance-Rankings und Effizienz-Matrix
  - Normalisierte Vergleichsmetriken für faire Bewertungen
- **🔄 Vergleiche**: 
  - Gleiche Modelle auf verschiedenen Servern
  - Verschiedene Modelle auf gleichem Server
  - Interaktive Balkengrafiken mit normalisierten Werten
  - Detailtabellen mit allen relevanten Spalten
- **📈 Qualitätsmetriken**: 
  - Radar-Charts für Metrik-Vergleiche
  - Box-Plots für Verteilungen
  - Detaillierte Statistiken

### Normalisierte Metriken für Vergleichbarkeit

Das Dashboard bietet normalisierte Metriken für faire Vergleiche zwischen Tests mit unterschiedlichen Konfigurationen:

- **Performance Normalized**: Token/s (bleibt unverändert, da bereits normalisiert)
- **Quality Normalized**: Durchschnittliche Qualitätsbewertung (bleibt unverändert)
- **Concurrent Efficiency**: Performance pro parallel Thread (Performance ÷ concurrent)
- **Throughput per Minute**: Fragen pro Minute basierend auf durchschnittlicher Antwortzeit
- **Load Efficiency**: Anteil der Netto-Inferenzzeit (ohne LLM-Ladezeit) in Prozent

Diese Metriken ermöglichen faire Vergleiche zwischen Tests mit unterschiedlichen `questions` und `concurrent` Einstellungen.

### Unterstützte Plattformen

- ✅ macOS
- ✅ Linux
- ✅ Windows

## Lizenz

MIT