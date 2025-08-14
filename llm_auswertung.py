#!/usr/bin/env python3
"""
LLM Auswertung - Streamlit Dashboard für LLM Stresstest Resultate
Analysiert und visualisiert alle JSON-Dateien im ./results Verzeichnis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pathlib import Path
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import glob
import os
import platform
import requests

# Windows-Kompatibilität sicherstellen
if platform.system() == 'Windows':
    import locale
    locale.setlocale(locale.LC_ALL, '')

# Streamlit Page Config
st.set_page_config(
    page_title="LLM Stresstest Auswertung",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS für bessere Darstellung
st.markdown("""
<style>
    /* Light Mode Metriken */
    .stMetric > div {
        padding: 15px;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Dark Mode Metriken */
    @media (prefers-color-scheme: dark) {
        .stMetric > div {
            background-color: #262730;
            border: 1px solid #404040;
            color: #ffffff;
        }
    }
    
    /* Streamlit Dark Theme Override */
    .stApp[data-theme="dark"] .stMetric > div {
        background-color: #262730 !important;
        border: 1px solid #404040 !important;
        color: #ffffff !important;
    }
    
    /* Fallback für dunkle Themes */
    div[data-testid="metric-container"] {
        background-color: var(--background-color, #ffffff) !important;
        border: 1px solid var(--border-color, #e0e0e0) !important;
        border-radius: 8px !important;
        padding: 15px !important;
        margin: 5px 0 !important;
    }
    
    .error-box {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 15px;
        margin: 10px 0;
        border-radius: 4px;
    }
    
    .warning-box {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 15px;
        margin: 10px 0;
        border-radius: 4px;
    }
    
    /* Bessere Kontraste für Dark Mode */
    .stApp[data-theme="dark"] .error-box {
        background-color: #4a1a1a !important;
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] .warning-box {
        background-color: #4a3a1a !important;
        color: #ffffff !important;
    }
    
    /* Button-Fixes für Lesbarkeit - ALLE Varianten abdecken */
    .stButton > button,
    div[data-testid="stButton"] > button,
    button[kind="primary"],
    button[kind="secondary"] {
        background-color: #0066cc !important;
        color: #ffffff !important;
        border: 2px solid #0066cc !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        min-width: 150px !important;
        height: 50px !important;
    }
    
    .stButton > button:hover,
    div[data-testid="stButton"] > button:hover,
    button[kind="primary"]:hover,
    button[kind="secondary"]:hover {
        background-color: #0052a3 !important;
        color: #ffffff !important;
    }
    
    .stButton > button[data-testid="baseButton-primary"] {
        background-color: #28a745 !important;
        border: 1px solid #28a745 !important;
        color: #ffffff !important;
    }
    
    .stButton > button[data-testid="baseButton-primary"]:hover {
        background-color: #218838 !important;
        color: #ffffff !important;
    }
    
    /* Log-Anzeige Kontrast Fixes */
    .error-box {
        background-color: #ffebee !important;
        color: #333333 !important;
        border-left: 4px solid #f44336;
        padding: 15px;
        margin: 10px 0;
        border-radius: 4px;
    }
    
    .warning-box {
        background-color: #fff3e0 !important;
        color: #333333 !important;
        border-left: 4px solid #ff9800;
        padding: 15px;
        margin: 10px 0;
        border-radius: 4px;
    }
    
    /* Metric Labels besser lesbar machen */
    .stMetric label {
        font-weight: 600 !important;
        color: inherit !important;
    }
    
    .stMetric [data-testid="metric-value"] {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: inherit !important;
    }
    
    /* DataFrames und Tabellen für Dark Mode */
    .stApp[data-theme="dark"] .stDataFrame {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] .stDataFrame table {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] .stDataFrame th {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border-bottom: 1px solid #404040 !important;
    }
    
    .stApp[data-theme="dark"] .stDataFrame td {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
        border-bottom: 1px solid #303030 !important;
    }
    
    /* Log-Nachrichten besser lesbar */
    .stApp[data-theme="dark"] .stMarkdown {
        color: #ffffff !important;
    }
    
    /* Selectbox und Input Felder */
    .stApp[data-theme="dark"] .stSelectbox > div > div {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] .stTextInput > div > div > input {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border: 1px solid #404040 !important;
    }
    
    /* Genereller Text-Kontrast Fix */
    .stApp[data-theme="dark"] * {
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] h1, 
    .stApp[data-theme="dark"] h2, 
    .stApp[data-theme="dark"] h3, 
    .stApp[data-theme="dark"] h4, 
    .stApp[data-theme="dark"] p,
    .stApp[data-theme="dark"] span,
    .stApp[data-theme="dark"] div {
        color: #ffffff !important;
    }
    
    /* Elegante Navigation Buttons */
    .stButton > button {
        width: 100% !important;
        border-radius: 10px !important;
        border: 1px solid #e0e0e0 !important;
        background: linear-gradient(145deg, #ffffff, #f0f0f0) !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1) !important;
        transition: all 0.3s ease !important;
        font-weight: 500 !important;
        padding: 15px 10px !important;
        margin: 5px 0 !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.15) !important;
        background: linear-gradient(145deg, #f8f9fa, #e9ecef) !important;
        border-color: #1f77b4 !important;
        color: #333333 !important;
    }
    
    .stButton > button:active {
        transform: translateY(0px) !important;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.1) !important;
        background: linear-gradient(145deg, #e9ecef, #dee2e6) !important;
    }
    
    /* Dark Mode Navigation */
    .stApp[data-theme="dark"] .stButton > button {
        background: linear-gradient(145deg, #2d2d2d, #1a1a1a) !important;
        border: 1px solid #404040 !important;
        color: #ffffff !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3) !important;
    }
    
    .stApp[data-theme="dark"] .stButton > button:hover {
        background: linear-gradient(145deg, #3d3d3d, #2a2a2a) !important;
        border-color: #1f77b4 !important;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.4) !important;
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] .stButton > button:active {
        background: linear-gradient(145deg, #1a1a1a, #0d0d0d) !important;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.3) !important;
    }
    
    /* Sidebar Styling */
    .stSidebar {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%) !important;
    }
    
    .stApp[data-theme="dark"] .stSidebar {
        background: linear-gradient(180deg, #2d2d2d 0%, #1a1a1a 100%) !important;
    }
    
    /* Fix für blaue Hover-Bereiche in Sidebar */
    .stSidebar .stButton > button {
        color: #333333 !important;
        background: linear-gradient(145deg, #ffffff, #f0f0f0) !important;
        border: 1px solid #e0e0e0 !important;
    }
    
    .stApp[data-theme="dark"] .stSidebar .stButton > button {
        color: #ffffff !important;
        background: linear-gradient(145deg, #2d2d2d, #1a1a1a) !important;
        border: 1px solid #404040 !important;
    }
    
    .stSidebar .stButton > button:hover {
        color: #333333 !important;
        background: linear-gradient(145deg, #f8f9fa, #e9ecef) !important;
        border-color: #1f77b4 !important;
    }
    
    .stApp[data-theme="dark"] .stSidebar .stButton > button:hover {
        color: #ffffff !important;
        background: linear-gradient(145deg, #3d3d3d, #2a2a2a) !important;
        border-color: #1f77b4 !important;
    }
    
    /* Fix für die kleinen blauen Bereiche unter den Buttons */
    .stSidebar .stButton > button:focus {
        color: #333333 !important;
        background: linear-gradient(145deg, #f8f9fa, #e9ecef) !important;
        border-color: #1f77b4 !important;
        outline: none !important;
    }
    
    .stApp[data-theme="dark"] .stSidebar .stButton > button:focus {
        color: #ffffff !important;
        background: linear-gradient(145deg, #3d3d3d, #2a2a2a) !important;
        border-color: #1f77b4 !important;
        outline: none !important;
    }
    
    /* Fix für alle Streamlit Button-Zustände in der Sidebar */
    .stSidebar .stButton button, 
    .stSidebar .stButton button:hover,
    .stSidebar .stButton button:focus,
    .stSidebar .stButton button:active {
        color: #333333 !important;
        background: linear-gradient(145deg, #ffffff, #f0f0f0) !important;
    }
    
    .stApp[data-theme="dark"] .stSidebar .stButton button,
    .stApp[data-theme="dark"] .stSidebar .stButton button:hover,
    .stApp[data-theme="dark"] .stSidebar .stButton button:focus,
    .stApp[data-theme="dark"] .stSidebar .stButton button:active {
        color: #ffffff !important;
        background: linear-gradient(145deg, #2d2d2d, #1a1a1a) !important;
    }
    
    /* Fix für die blauen Container-Bereiche */
    .stSidebar > div > div {
        background: transparent !important;
    }
    
    .stSidebar .element-container {
        background: transparent !important;
    }
    
    .stSidebar .stButton {
        background: transparent !important;
    }
    
    /* Aggressive Fixes für alle möglichen blauen Bereiche */
    .stApp[data-theme="dark"] .stSidebar * {
        color: #ffffff !important;
    }
    
    .stSidebar * {
        color: #333333 !important;
    }
    
    /* Log-Level Farben für DataFrames */
    .stDataFrame [data-testid="stDataFrame"] tbody tr:has(td:nth-child(3):contains("ERROR")) {
        background-color: #ffebee !important;
    }
    
    .stDataFrame [data-testid="stDataFrame"] tbody tr:has(td:nth-child(3):contains("WARNING")) {
        background-color: #fff3e0 !important;
    }
    
    .stDataFrame [data-testid="stDataFrame"] tbody tr:has(td:nth-child(3):contains("INFO")) {
        background-color: #e3f2fd !important;
    }
    
    .stDataFrame [data-testid="stDataFrame"] tbody tr:has(td:nth-child(3):contains("DEBUG")) {
        background-color: #f3e5f5 !important;
    }
    
    /* Dark Mode Log-Level Farben */
    .stApp[data-theme="dark"] .stDataFrame [data-testid="stDataFrame"] tbody tr:has(td:nth-child(3):contains("ERROR")) {
        background-color: #4a1a1a !important;
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] .stDataFrame [data-testid="stDataFrame"] tbody tr:has(td:nth-child(3):contains("WARNING")) {
        background-color: #4a3a1a !important;
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] .stDataFrame [data-testid="stDataFrame"] tbody tr:has(td:nth-child(3):contains("INFO")) {
        background-color: #1a2a4a !important;
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] .stDataFrame [data-testid="stDataFrame"] tbody tr:has(td:nth-child(3):contains("DEBUG")) {
        background-color: #2a1a4a !important;
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] .stSidebar {
        background: linear-gradient(180deg, #2d2d2d 0%, #1a1a1a 100%) !important;
    }
    
    /* Aktive Navigation hervorheben */
    .nav-active > button {
        background: linear-gradient(145deg, #1f77b4, #0d47a1) !important;
        color: white !important;
        border-color: #1565c0 !important;
        box-shadow: inset 2px 2px 5px rgba(0,0,0,0.2) !important;
    }
    
    /* Custom Dashboard Header */
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Sidebar Info Boxes */
    .sidebar-info {
        background: linear-gradient(145deg, #e3f2fd, #bbdefb);
        border-left: 4px solid #2196f3;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        font-size: 0.9rem;
    }
    
    .stApp[data-theme="dark"] .sidebar-info {
        background: linear-gradient(145deg, #1a237e, #0d47a1);
        border-left: 4px solid #64b5f6;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)


class LLMAnalyzer:
    """Klasse zur Analyse von LLM Stresstest Resultaten"""
    
    def __init__(self):
        self.results_path = Path('./results')
        self.log_path = Path('logs')
        self.config_path = Path('./config')
        self.data = []
        self.logs = []
        self.models_info = {}
        self.load_models_info()
    
    def load_models_info(self):
        """Lädt Model-Informationen aus config/models.json"""
        models_file = self.config_path / 'models.json'
        if models_file.exists():
            try:
                with open(models_file, 'r', encoding='utf-8') as f:
                    models_data = json.load(f)
                    self.models_info = models_data.get('models', {})
            except Exception as e:
                print(f"Warning: Could not load models.json: {e}")
                self.models_info = {}
        
    def load_all_results(self) -> List[Dict]:
        """Lädt alle JSON-Dateien aus dem results Verzeichnis"""
        json_files = list(self.results_path.glob('*.json'))
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['filename'] = file_path.name
                    self.data.append(data)
            except Exception as e:
                st.warning(f"Fehler beim Laden von {file_path.name}: {e}")
        
        return self.data
    
    def load_logs(self) -> List[Dict]:
        """Lädt alle Log-Dateien"""
        log_files = list(self.log_path.glob('llm_stresstest_*.log'))
        
        for file_path in log_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                    for line in lines:
                        # Parse log line
                        match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\S+) - (\w+) - (.+)', line)
                        if match:
                            self.logs.append({
                                'timestamp': match.group(1),
                                'module': match.group(2),
                                'level': match.group(3),
                                'message': match.group(4),
                                'file': file_path.name
                            })
            except Exception as e:
                st.warning(f"Fehler beim Laden von {file_path.name}: {e}")
        
        return self.logs
    
    def get_dataframe(self) -> pd.DataFrame:
        """Erstellt DataFrame aus allen Resultaten"""
        rows = []
        for result in self.data:
            meta = result.get('meta', {})
            aggregate = result.get('aggregate', {})
            
            model_name = meta.get('model', 'Unknown')
            
            row = {
                'filename': result['filename'],
                'server': meta.get('server_name', meta.get('server', 'Unknown')),  # Nutze server_name, fallback auf server/URL
                'server_url': meta.get('server', 'Unknown'),
                'model': model_name,
                'questions': meta.get('questions', 0),
                'concurrent': meta.get('concurrent', 1),
                'total_duration_ms': meta.get('total_duration_ms', 0),
                'runtime_avg': aggregate.get('runtime_avg', 0),
                'token_avg': aggregate.get('token_avg', 0),
                'quality_avg': aggregate.get('quality_avg', 0),
                'llm_load_time': aggregate.get('llm_load_time', 0),
                'cold_start_factor': aggregate.get('cold_start_factor', 0),
                'start_time': meta.get('start_time', ''),
                'start_date': meta.get('start_date', ''),
                # Modell-Metadaten (falls verfügbar)
                'parameter_size': meta.get('parameter_size', 'Unknown'),
                'quantization_level': meta.get('quantization_level', 'Unknown'),
                'size_bytes': meta.get('size_bytes', 0),
                'family': meta.get('family', 'Unknown')
            }
            
            # Model-Eigenschaften aus models.json hinzufügen
            if model_name in self.models_info:
                model_info = self.models_info[model_name]
                row['multimodal'] = model_info.get('multimodal', False)
                row['tools_support'] = model_info.get('tools_support', False)
                row['reasoning_optimized'] = model_info.get('reasoning_optimized', False)
                row['size_category'] = model_info.get('size_category', 'unknown')
                row['model_type'] = model_info.get('model_type', 'unknown')
                row['provider'] = model_info.get('provider', 'unknown')
            else:
                # Defaults wenn nicht in models.json
                row['multimodal'] = False
                row['tools_support'] = False
                row['reasoning_optimized'] = False
                row['size_category'] = 'unknown'
                row['model_type'] = 'unknown'
                row['provider'] = 'unknown'
            
            # Performance berechnen (Token/Zeit)
            if row['runtime_avg'] > 0:
                row['performance'] = round(row['token_avg'] / (row['runtime_avg'] / 1000), 2)
            else:
                row['performance'] = 0
            
            # Normalisierte Metriken für Vergleichbarkeit
            questions_count = row['questions'] if row['questions'] > 0 else 1
            concurrent_factor = row['concurrent'] if row['concurrent'] > 0 else 1
            
            # Normalisierte Performance (pro Frage, sequential)
            row['performance_normalized'] = row['performance']  # Token/s bleibt gleich
            
            # Normalisierte Qualität (bleibt gleich, da durchschnittlich)
            row['quality_normalized'] = row['quality_avg']
            
            # Concurrent-Effizienz (Performance pro concurrent thread)
            row['concurrent_efficiency'] = round(row['performance'] / concurrent_factor, 2) if concurrent_factor > 0 else 0
            
            # Durchsatz pro Minute (normalisiert)
            if row['runtime_avg'] > 0:
                row['throughput_per_min'] = round((60 * 1000) / row['runtime_avg'], 2)  # Fragen pro Minute
            else:
                row['throughput_per_min'] = 0
            
            # Load time efficiency (Load time vs Runtime)
            if row['runtime_avg'] > 0:
                row['load_efficiency'] = round((row['runtime_avg'] - row['llm_load_time']) / row['runtime_avg'] * 100, 1)
            else:
                row['load_efficiency'] = 0
            
            # Performance pro Parameter (falls Parameter-Info verfügbar)
            row['performance_per_billion_params'] = 0
            if row['parameter_size'] != 'Unknown' and row['parameter_size']:
                try:
                    # Parse Parameter-Größe (z.B. "14.8B" -> 14.8)
                    param_str = str(row['parameter_size']).upper()
                    if param_str.endswith('B'):
                        param_billions = float(param_str[:-1])
                        if param_billions > 0:
                            row['performance_per_billion_params'] = round(row['performance'] / param_billions, 2)
                    elif param_str.endswith('M'):
                        # Für kleinere Modelle in Millionen
                        param_millions = float(param_str[:-1])
                        param_billions = param_millions / 1000
                        if param_billions > 0:
                            row['performance_per_billion_params'] = round(row['performance'] / param_billions, 2)
                except (ValueError, ZeroDivisionError):
                    pass
            
            # Modellgröße in GB (falls verfügbar)
            row['size_gb'] = 0
            if row['size_bytes'] is not None and row['size_bytes'] > 0:
                row['size_gb'] = round(row['size_bytes'] / (1024**3), 1)
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def get_detailed_quality_metrics(self) -> pd.DataFrame:
        """Erstellt DataFrame mit detaillierten Qualitätsmetriken"""
        rows = []
        for result in self.data:
            meta = result.get('meta', {})
            
            for item in result.get('results', []):
                if 'quality_metrics' in item and item['quality_metrics']:
                    metrics = item['quality_metrics']
                    row = {
                        'filename': result['filename'],
                        'server': meta.get('server', 'Unknown'),
                        'model': meta.get('model', 'Unknown'),
                        'question': item.get('question', '')[:50] + '...',
                        **metrics
                    }
                    rows.append(row)
        
        return pd.DataFrame(rows)


def main():
    # Header mit Filter-Status
    header_col1, header_col2 = st.columns([3, 1])
    
    with header_col1:
        st.title("🔬 Finken's LLM Stresstest Dashboard")
    
    with header_col2:
        # Platzhalter für Filter-Status (wird später gesetzt)
        filter_placeholder = st.empty()
    
    # GLOBALES CSS FÜR ALLE BUTTONS
    st.markdown("""
    <style>
    /* Force-Override für ALLE Streamlit Buttons */
    [data-testid="stButton"] > button {
        background-color: #0066cc !important;
        color: white !important;
        border: 2px solid #0066cc !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        min-width: 150px !important;
        height: 50px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(0,102,204,0.2) !important;
    }
    
    [data-testid="stButton"] > button:hover {
        background-color: #0052a3 !important;
        border-color: #0052a3 !important;
        box-shadow: 0 4px 8px rgba(0,102,204,0.3) !important;
        transform: translateY(-1px) !important;
    }
    
    [data-testid="stButton"] > button:active {
        transform: translateY(0px) !important;
        box-shadow: 0 2px 4px rgba(0,102,204,0.2) !important;
    }
    
    /* Sidebar buttons special styling */
    section[data-testid="stSidebar"] [data-testid="stButton"] > button {
        min-width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Analyzer initialisieren
    analyzer = LLMAnalyzer()
    
    # Navigation mit custom styling
    nav_options = {
        "📊 Übersicht": {"icon": "📊", "desc": "Gesamtstatistiken & Übersicht"},
        "⚡ Stresstest": {"icon": "⚡", "desc": "Stresstest-Konfiguration & Start"},
        "🤖 Model-Information": {"icon": "🤖", "desc": "Detaillierte Model-Eigenschaften"},
        "📝 Logs": {"icon": "📝", "desc": "Log-Analyse & Fehlersuche"},
        "⚡ Performance": {"icon": "⚡", "desc": "Performance & Ladezeiten"},
        "🔄 Vergleiche": {"icon": "🔄", "desc": "Server & Modell-Vergleiche"},
        "📈 Qualitätsmetriken": {"icon": "📈", "desc": "Detaillierte Qualitätsanalyse"}
    }
    
    # Custom Radio Buttons mit Beschreibungen
    selected_page = None
    for i, (page_name, info) in enumerate(nav_options.items()):
        # Extrahiere den Text ohne Icon (alles nach erstem Space, oder ganzer Text wenn kein Space)
        button_text = page_name.split(' ', 1)[1] if ' ' in page_name else page_name
        if st.sidebar.button(
            f"{info['icon']} {button_text}",
            key=f"nav_{i}",
            use_container_width=True
        ):
            st.session_state.current_page = page_name
    
    # Fallback: Wenn keine Seite gesetzt, nimm die erste
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "📊 Übersicht"
    
    page = st.session_state.current_page
    
    # Daten laden
    with st.spinner("Lade Daten..."):
        results = analyzer.load_all_results()
        
        # Logs mit Cache laden (für Refresh-Funktionalität)
        if 'log_cache' not in st.session_state:
            st.session_state.log_cache = analyzer.load_logs()
        logs = st.session_state.log_cache
    
    if not results:
        st.error("❌ Keine Result-Dateien im ./results Verzeichnis gefunden!")
        st.info("Führe zuerst einen Stresstest aus: `python llm_stresstest.py <output_name>`")
        return
    
    df = analyzer.get_dataframe()
    
    
    # Filter-Optionen für Model-Eigenschaften
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Filter nach Model-Eigenschaften")
    
    # Size Category Filter
    size_categories = ['all'] + sorted(df['size_category'].unique().tolist())
    selected_size = st.sidebar.selectbox(
        "Modellgröße:",
        size_categories,
        index=0,
        help="Filtere nach Modellgröße (tiny < 1B, small 1-3B, medium 3-10B, large 10-30B, xlarge 30-100B)"
    )
    
    # Model Type Filter  
    model_types = ['all'] + sorted(df['model_type'].unique().tolist())
    selected_type = st.sidebar.selectbox(
        "Modell-Typ:",
        model_types,
        index=0,
        help="Filtere nach Modell-Typ (chat, instruct, base, reasoning, code)"
    )
    
    # Feature Toggles
    st.sidebar.markdown("**Spezielle Features:**")
    
    # Feature Toggles ohne Info-Buttons
    filter_reasoning = st.sidebar.checkbox(
        "Nur Reasoning-optimierte",
        value=False,
        key="reasoning_filter",
        help="Zeigt nur Modelle die für logisches Denken optimiert sind"
    )
    
    filter_multimodal = st.sidebar.checkbox(
        "Nur Multimodale",
        value=False,
        key="multimodal_filter",
        help="Zeigt nur Modelle die Bilder verarbeiten können"
    )
    
    filter_tools = st.sidebar.checkbox(
        "Nur mit Tool-Support",
        value=False,
        key="tools_filter",
        help="Zeigt nur Modelle die Function Calling unterstützen"
    )
    
    st.sidebar.markdown("---")
    
    # Daten filtern basierend auf Auswahl
    filtered_df = df.copy()
    active_filters = []
    
    if selected_size != 'all':
        filtered_df = filtered_df[filtered_df['size_category'] == selected_size]
        active_filters.append(f"Größe: {selected_size.upper()}")
    
    if selected_type != 'all':
        filtered_df = filtered_df[filtered_df['model_type'] == selected_type]
        active_filters.append(f"Typ: {selected_type.upper()}")
    
    if filter_reasoning:
        filtered_df = filtered_df[filtered_df['reasoning_optimized'] == True]
        active_filters.append("🧠 Reasoning")
    
    if filter_multimodal:
        filtered_df = filtered_df[filtered_df['multimodal'] == True]
        active_filters.append("🖼️ Multimodal")
    
    if filter_tools:
        filtered_df = filtered_df[filtered_df['tools_support'] == True]
        active_filters.append("🔧 Tools")
    
    # Zeige Filter-Status
    filters_active = len(filtered_df) < len(df)
    st.session_state.filters_active = filters_active
    st.session_state.active_filters = active_filters
    
    # Filter-Status oben rechts anzeigen
    if filters_active and active_filters:
        filter_text = " | ".join(active_filters)
        filter_placeholder.markdown(f"""
        <div style="
            background-color: #ff4b4b;
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: bold;
            text-align: center;
            margin-top: 10px;
        ">
        🔍 GEFILTERT: {filter_text}
        </div>
        """, unsafe_allow_html=True)
    
    if filters_active:
        st.sidebar.info(f"📊 {len(filtered_df)} von {len(df)} Tests angezeigt")
    
    # Verwende filtered_df statt df für alle Visualisierungen
    df = filtered_df
    
    # Sidebar Info
    st.sidebar.markdown("---")
    st.sidebar.info(f"📁 {len(results)} Result-Dateien geladen")
    st.sidebar.info(f"📝 {len(logs)} Log-Einträge gefunden")
    
    # Hauptinhalt basierend auf Auswahl
    if page == "📊 Übersicht":
        show_overview(df, results)
    elif page == "🤖 Model-Information":
        show_model_information(analyzer, df, results)
    elif page == "📝 Logs":
        show_logs(logs)
    elif page == "⚡ Performance":
        show_performance(df, results)
    elif page == "🔄 Vergleiche":
        show_comparisons(df, results)
    elif page == "📈 Qualitätsmetriken":
        show_quality_metrics(analyzer, results)
    elif page == "⚡ Stresstest":
        show_configuration(results)


def show_model_information(analyzer: LLMAnalyzer, df: pd.DataFrame, results: List[Dict]):
    """Zeigt detaillierte Model-Informationen"""
    st.header("🤖 Model-Information")
    
    # Info-Bereiche für Feature-Erklärungen
    st.subheader("📚 Feature-Definitionen")
    
    # Reasoning-optimierte Modelle Info
    reasoning_expanded = st.session_state.get('show_reasoning_info', False)
    with st.expander("🧠 **Reasoning-optimierte Modelle**", expanded=reasoning_expanded):
        st.markdown("""
        **Reasoning-optimierte Modelle:**
        
        Diese Modelle sind speziell darauf trainiert, komplexe logische Denkprozesse durchzuführen. Sie können:
        
        • **Schrittweise Problemlösung**: Komplexe Aufgaben in kleinere Schritte zerlegen  
        • **Mathematische Beweisführung**: Logische Schlussfolgerungen und Beweise erstellen  
        • **Kausale Zusammenhänge**: Ursache-Wirkungs-Beziehungen besser verstehen  
        • **Selbstreflexion**: Eigene Antworten hinterfragen und korrigieren  
        
        **Beispiele:** DeepSeek-R1, OpenAI o1, Claude-3.5-Sonnet mit Chain-of-Thought
        
        Diese Modelle sind besonders gut für wissenschaftliche Analysen, Programmierung und komplexe Entscheidungsfindung geeignet.
        """)
        if reasoning_expanded:
            st.session_state.show_reasoning_info = False  # Reset nach dem Anzeigen
    
    # Multimodale Modelle Info  
    multimodal_expanded = st.session_state.get('show_multimodal_info', False)
    with st.expander("👁️ **Multimodale Modelle**", expanded=multimodal_expanded):
        st.markdown("""
        **Multimodale Modelle:**
        
        Diese Modelle können verschiedene Eingabetypen verarbeiten und verstehen:
        
        • **Bilder verstehen**: Fotos, Diagramme, Screenshots analysieren  
        • **Dokumente lesen**: PDFs, Tabellen, Charts interpretieren  
        • **Vision + Text**: Bildbeschreibungen, OCR, visuelle Fragen beantworten  
        • **Grafiken erstellen**: Teilweise auch Bildsynthese möglich  
        
        **Beispiele:** GPT-4V, Claude-3-Vision, Gemini-Pro-Vision, LLaVA
        
        **Anwendungen:**  
        - Dokumentenanalyse  
        - Medizinische Bildauswertung  
        - UI/UX Design-Feedback  
        - Barrierefreiheit (Alt-Text Generierung)
        """)
        if multimodal_expanded:
            st.session_state.show_multimodal_info = False  # Reset nach dem Anzeigen
    
    # Tool-Support Info
    tools_expanded = st.session_state.get('show_tools_info', False)
    with st.expander("🔧 **Tool-Support (Function Calling)**", expanded=tools_expanded):
        st.markdown("""
        **Tool-Support (Function Calling):**
        
        Diese Modelle können externe Tools und APIs aufrufen:
        
        • **API-Integration**: REST APIs, Datenbanken, Web-Services nutzen  
        • **Code-Ausführung**: Python-Scripts, Shell-Commands ausführen  
        • **Berechnungen**: Mathematische Operationen über externe Tools  
        • **Real-time Daten**: Aktuelle Informationen abrufen (Wetter, Börse, etc.)  
        
        **Technische Details:**  
        - Strukturierte JSON-Funktionsaufrufe  
        - Parameter-Validierung und -Mapping  
        - Fehlerbehandlung bei Tool-Fehlern  
        - Verkettung mehrerer Tool-Aufrufe  
        
        **Beispiele:** GPT-4-Turbo, Claude-3-Sonnet, Mistral-Large
        
        **Anwendungen:**  
        - Automatisierte Workflows  
        - Datenanalyse und Reporting  
        - Smart Home Integration  
        - Business Process Automation
        """)
        if tools_expanded:
            st.session_state.show_tools_info = False  # Reset nach dem Anzeigen
        
    st.markdown("---")
    
    # Model-Auswahl
    tested_models = sorted(df['model'].unique())
    
    if not tested_models:
        st.warning("Keine Modelle in den Test-Ergebnissen gefunden!")
        return
    
    selected_model = st.selectbox(
        "📌 Wähle ein Modell für Details:",
        tested_models,
        index=0
    )
    
    # Filtere Daten für das gewählte Modell
    model_df = df[df['model'] == selected_model]
    
    # Model-Info aus Registry
    model_info = analyzer.models_info.get(selected_model, {})
    
    # Layout mit zwei Spalten
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("📋 Model-Eigenschaften")
        
        if model_info:
            # Badge-Style Properties
            st.markdown("**Features:**")
            features = []
            if model_info.get('reasoning_optimized', False):
                features.append("🧠 Reasoning")
            if model_info.get('multimodal', False):
                features.append("🖼️ Multimodal")
            if model_info.get('tools_support', False):
                features.append("🔧 Tools")
            
            if features:
                st.markdown(" | ".join(features))
            else:
                st.markdown("*Keine speziellen Features*")
            
            st.markdown("---")
            
            # Detaillierte Eigenschaften
            props_data = {
                "Provider": model_info.get('provider', 'unknown'),
                "Model Type": model_info.get('model_type', 'unknown'),
                "Size Category": model_info.get('size_category', 'unknown'),
                "Parameters": f"{model_info.get('parameters', 0):,}" if model_info.get('parameters') else 'unknown',
                "Info Quality": model_info.get('info_quality', 'unknown'),
                "Sources": ", ".join(model_info.get('sources', [])) if model_info.get('sources') else 'none'
            }
            
            # Festplattengröße aus DataFrame holen (falls verfügbar)
            if not model_df.empty and 'size_gb' in model_df.columns:
                size_gb = model_df['size_gb'].iloc[0]
                if pd.notna(size_gb) and size_gb > 0:
                    props_data["Festplattengröße"] = f"{size_gb} GB"
                else:
                    props_data["Festplattengröße"] = "unbekannt"
            else:
                props_data["Festplattengröße"] = "unbekannt"
            
            for key, value in props_data.items():
                st.markdown(f"**{key}:** {value}")
            
            # Zusätzliche Metadaten wenn verfügbar
            if 'tags' in model_info and model_info['tags']:
                st.markdown("**Tags:**")
                tags_str = ", ".join(model_info['tags'][:5])
                st.markdown(f"*{tags_str}*")
        else:
            st.info("ℹ️ Keine detaillierten Informationen in der Model Registry")
            st.markdown("Führe `python update_model_registry.py` aus")
    
    with col2:
        st.subheader("📊 Performance nach Server")
        
        # Performance-Vergleich über Server
        server_perf = model_df.groupby('server').agg({
            'performance': 'mean',
            'runtime_avg': 'mean',
            'quality_avg': 'mean',
            'token_avg': 'mean'
        }).round(2)
        
        if not server_perf.empty:
            # Bar Chart für Performance
            fig_perf = px.bar(
                server_perf.reset_index(),
                x='server',
                y='performance',
                title=f'Performance von {selected_model} auf verschiedenen Servern',
                labels={'performance': 'Tokens/Sekunde', 'server': 'Server'},
                color='performance',
                color_continuous_scale='Viridis',
                text='performance'
            )
            fig_perf.update_traces(texttemplate='%{text:.1f} T/s', textposition='outside')
            fig_perf.update_layout(height=400)
            st.plotly_chart(fig_perf, use_container_width=True)
    
    # Qualitäts-Übersicht
    st.markdown("---")
    st.subheader("🎯 Qualitäts-Analyse")
    
    col3, col4, col5, col6 = st.columns(4)
    
    avg_quality = model_df['quality_avg'].mean()
    avg_runtime = model_df['runtime_avg'].mean()
    avg_tokens = model_df['token_avg'].mean()
    test_count = len(model_df)
    
    with col3:
        st.metric("Ø Qualität", f"{avg_quality:.3f}", 
                 help="Durchschnittliche Qualität über alle Tests")
    with col4:
        st.metric("Ø Laufzeit", f"{avg_runtime:.1f} ms",
                 help="Durchschnittliche Antwortzeit")
    with col5:
        st.metric("Ø Tokens", f"{avg_tokens:.0f}",
                 help="Durchschnittliche Token-Anzahl")
    with col6:
        st.metric("Tests", test_count,
                 help="Anzahl durchgeführter Tests")
    
    # Detaillierte Test-Ergebnisse
    st.markdown("---")
    st.subheader("📈 Test-Ergebnisse im Detail")
    
    # Zeige alle Tests für dieses Modell
    detail_cols = ['server', 'questions', 'concurrent', 'runtime_avg', 'token_avg', 
                   'quality_avg', 'performance', 'start_date', 'start_time']
    detail_df = model_df[detail_cols].copy()
    detail_df = detail_df.sort_values('start_date', ascending=False)
    
    st.dataframe(
        detail_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'server': st.column_config.TextColumn('Server'),
            'questions': st.column_config.NumberColumn('Fragen'),
            'concurrent': st.column_config.NumberColumn('Concurrent'),
            'runtime_avg': st.column_config.NumberColumn('Ø Zeit (ms)', format="%.1f"),
            'token_avg': st.column_config.NumberColumn('Ø Tokens'),
            'quality_avg': st.column_config.NumberColumn('Ø Qualität', format="%.3f"),
            'performance': st.column_config.NumberColumn('Performance (T/s)', format="%.2f"),
            'start_date': st.column_config.TextColumn('Datum'),
            'start_time': st.column_config.TextColumn('Zeit')
        }
    )
    
    # Ähnliche/Vergleichbare Modelle
    st.markdown("---")
    st.subheader("🔗 Ähnliche & Vergleichbare Modelle")
    
    similar_models = find_similar_models(selected_model, analyzer.models_info, df)
    
    if similar_models:
        col7, col8 = st.columns(2)
        
        with col7:
            st.markdown("**🎯 Gleiche Größenkategorie:**")
            size_similar = similar_models.get('same_size', [])
            if size_similar:
                for model in size_similar[:5]:
                    st.markdown(f"• {model}")
            else:
                st.markdown("*Keine gefunden*")
        
        with col8:
            st.markdown("**🏷️ Gleicher Typ:**")
            type_similar = similar_models.get('same_type', [])
            if type_similar:
                for model in type_similar[:5]:
                    st.markdown(f"• {model}")
            else:
                st.markdown("*Keine gefunden*")
        
        # Empfehlungen
        if similar_models.get('recommendations'):
            st.info("💡 **Empfohlene Vergleiche:** " + ", ".join(similar_models['recommendations'][:3]))
    else:
        st.info("Keine ähnlichen Modelle in den Tests gefunden")


def find_similar_models(selected_model: str, models_info: Dict, df: pd.DataFrame) -> Dict:
    """Findet ähnliche und vergleichbare Modelle"""
    if selected_model not in models_info:
        return {}
    
    model_info = models_info[selected_model]
    tested_models = df['model'].unique()
    
    similar = {
        'same_size': [],
        'same_type': [],
        'same_provider': [],
        'recommendations': []
    }
    
    for other_model in tested_models:
        if other_model == selected_model:
            continue
        
        if other_model in models_info:
            other_info = models_info[other_model]
            
            # Gleiche Größenkategorie
            if other_info.get('size_category') == model_info.get('size_category'):
                similar['same_size'].append(other_model)
            
            # Gleicher Typ
            if other_info.get('model_type') == model_info.get('model_type'):
                similar['same_type'].append(other_model)
            
            # Gleicher Provider
            if other_info.get('provider') == model_info.get('provider'):
                similar['same_provider'].append(other_model)
    
    # Empfehlungen generieren
    recommendations = []
    
    # Beste Vergleiche: Gleiche Größe UND gleicher Typ
    best_matches = set(similar['same_size']) & set(similar['same_type'])
    if best_matches:
        recommendations.extend(list(best_matches)[:2])
    
    # Alternativ: Gleiche Größe
    if len(recommendations) < 3 and similar['same_size']:
        for model in similar['same_size']:
            if model not in recommendations:
                recommendations.append(model)
                if len(recommendations) >= 3:
                    break
    
    similar['recommendations'] = recommendations
    
    return similar


def show_overview(df: pd.DataFrame, results: List[Dict]):
    """Zeigt Übersichtsseite"""
    st.header("Gesamtübersicht")
    
    # Kompakte Metriken-Übersicht in einer Zeile
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    
    with col1:
        st.metric("Tests", len(results))
    with col2:
        st.metric("Modelle", df['model'].nunique())
    with col3:
        st.metric("Server", df['server'].nunique())
    with col4:
        avg_quality = df['quality_avg'].mean()
        st.metric("Ø Qualität", f"{avg_quality:.3f}" if not pd.isna(avg_quality) else "N/A")
    
    with col5:
        reasoning_models = df[df['reasoning_optimized'] == True]['model'].nunique()
        st.metric("Reasoning", reasoning_models, 
                 help="Modelle mit Reasoning-Optimierung")
    
    with col6:
        multimodal_models = df[df['multimodal'] == True]['model'].nunique()
        st.metric("Multimodal", multimodal_models,
                 help="Modelle mit Bildverarbeitung")
    
    with col7:
        tools_models = df[df['tools_support'] == True]['model'].nunique()
        st.metric("Tools", tools_models,
                 help="Modelle mit Function-Calling")
    
    with col8:
        # Größenverteilung
        size_dist = df.groupby('size_category')['model'].nunique()
        most_common_size = size_dist.idxmax() if not size_dist.empty else "unknown"
        st.metric("Größe", most_common_size.upper(),
                 help=f"Häufigste Größe, Verteilung: {dict(size_dist)}")
    
    st.markdown("---")
    
    # Vergleichbarkeits-Hinweis
    questions_variance = df['questions'].nunique()
    concurrent_variance = df['concurrent'].nunique()
    
    if questions_variance > 1 or concurrent_variance > 1:
        questions_list = [int(x) for x in sorted(df['questions'].unique())]
        concurrent_list = [int(x) for x in sorted(df['concurrent'].unique())]
        
        st.info(f"""
        ℹ️ **Vergleichbarkeit**: Die Tests verwenden unterschiedliche Konfigurationen:
        - {questions_variance} verschiedene Fragen-Anzahlen: {questions_list}
        - {concurrent_variance} verschiedene Concurrent-Einstellungen: {concurrent_list}
        
        Für faire Vergleiche werden normalisierte Metriken verwendet (siehe Performance-Bereich).
        """)
    
    # Übersichtstabelle
    st.subheader("📋 Alle Tests")
    
    # Spalten auswählen - erweitert um Model-Eigenschaften (ohne filename)
    display_cols = ['server', 'model', 'size_category', 'model_type', 
                    'reasoning_optimized', 'multimodal', 'tools_support',
                    'parameter_size', 'quantization_level', 'questions', 'concurrent', 
                    'runtime_avg', 'token_avg', 'quality_avg', 'performance']
    
    # Prüfe welche Spalten existieren
    available_cols = [col for col in display_cols if col in df.columns]
    display_df = df[available_cols].copy()
    
    # Formatierung
    display_df['runtime_avg'] = display_df['runtime_avg'].round(1)
    display_df['quality_avg'] = display_df['quality_avg'].round(3)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'server': st.column_config.TextColumn('Server'),
            'model': st.column_config.TextColumn('Modell'),
            'parameter_size': st.column_config.TextColumn('Parameter'),
            'quantization_level': st.column_config.TextColumn('Quantisierung'),
            'size_gb': st.column_config.NumberColumn('Größe (GB)', format="%.1f"),
            'questions': st.column_config.NumberColumn('Fragen'),
            'concurrent': st.column_config.NumberColumn('Parallel'),
            'runtime_avg': st.column_config.NumberColumn('Ø Zeit (ms)', format="%.1f"),
            'token_avg': st.column_config.NumberColumn('Ø Tokens'),
            'quality_avg': st.column_config.NumberColumn('Ø Qualität', format="%.3f"),
            'performance': st.column_config.NumberColumn('Performance (T/s)', format="%.2f"),
            'performance_per_billion_params': st.column_config.NumberColumn('Effizienz (T/s/B)', format="%.2f")
        }
    )
    
    st.markdown("---")
    
    # Performance-Kuchendiagramme
    st.subheader("🥧 Performance-Verteilung")
    st.caption("Anteil der verschiedenen Server und Modelle an der Gesamtperformance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Server-Performance Kuchendiagramm
        server_performance = df.groupby('server')['performance'].sum().reset_index()
        server_performance = server_performance.sort_values('performance', ascending=False)
        
        fig_server_pie = px.pie(
            server_performance,
            values='performance',
            names='server',
            title='Server-Performance Anteil',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_server_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Performance: %{value:.1f} T/s<br>Anteil: %{percent}<extra></extra>'
        )
        st.plotly_chart(fig_server_pie, use_container_width=True)
    
    with col2:
        # Modell-Performance Kuchendiagramm
        model_performance = df.groupby('model')['performance'].sum().reset_index()
        model_performance = model_performance.sort_values('performance', ascending=False)
        
        # Lange Modellnamen kürzen für bessere Anzeige
        model_performance['model_short'] = model_performance['model'].str.replace(':latest', '').str.replace(':12b', '')
        
        fig_model_pie = px.pie(
            model_performance,
            values='performance',
            names='model_short',
            title='Modell-Performance Anteil',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_model_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Performance: %{value:.1f} T/s<br>Anteil: %{percent}<extra></extra>'
        )
        st.plotly_chart(fig_model_pie, use_container_width=True)
    
    
    # Globale Performance-Analyse aller LLMs
    st.subheader("🚀 Globale Performance-Analyse")
    st.caption("Performance aller getesteten LLMs über alle Server hinweg")
    
    # Performance-Ranking aller LLMs (normalisiert)
    perf_ranking = df.groupby('model').agg({
        'performance': ['mean', 'max', 'min', 'count'],
        'concurrent_efficiency': 'mean',
        'throughput_per_min': 'mean',
        'quality_avg': 'mean'
    }).round(2)
    
    # Flatten column names
    perf_ranking.columns = ['_'.join(col).strip() for col in perf_ranking.columns]
    perf_ranking = perf_ranking.reset_index()
    perf_ranking = perf_ranking.sort_values('performance_mean', ascending=False)
    
    # Performance-Chart - Ein Eintrag je Modell+Server
    df_perf = df.copy()
    df_perf['model_short'] = df_perf['model'].str.replace(':latest', '').str.replace(':12b', '').str.replace(':14b', '').str.replace(':8b', '')
    df_perf['server_short'] = df_perf['server'].str.replace('MacBook Pro ', 'MBP ').str.replace('localhost', 'Local')
    df_perf['display_name'] = df_perf['model_short'] + '<br>' + df_perf['server_short']
    
    fig_perf_global = px.bar(
        df_perf.sort_values('performance', ascending=False),
        x='display_name',
        y='performance',
        color='server',
        title='Performance nach Modell und Server',
        labels={'performance': 'Performance (T/s)', 'display_name': 'Modell + Server'},
        hover_data=['model', 'server', 'questions', 'concurrent']
    )
    fig_perf_global.update_layout(
        height=500,
        xaxis_title="Modell + Server",
        showlegend=True,
        legend=dict(title="Server")
    )
    st.plotly_chart(fig_perf_global, use_container_width=True)
    
    # Performance-Ranking Tabelle
    st.dataframe(
        perf_ranking,
        use_container_width=True,
        hide_index=True,
        column_config={
            'model': st.column_config.TextColumn('Modell'),
            'performance_mean': st.column_config.NumberColumn('Ø Performance (T/s)', format="%.2f"),
            'performance_max': st.column_config.NumberColumn('Max Performance', format="%.2f"),
            'performance_min': st.column_config.NumberColumn('Min Performance', format="%.2f"),
            'performance_count': st.column_config.NumberColumn('Tests'),
            'concurrent_efficiency_mean': st.column_config.NumberColumn('Ø Concurrent-Eff.', format="%.2f"),
            'throughput_per_min_mean': st.column_config.NumberColumn('Ø Durchsatz (/min)', format="%.2f"),
            'quality_avg_mean': st.column_config.NumberColumn('Ø Qualität', format="%.3f")
        }
    )
    
    st.markdown("---")
    
    # Globale Qualitäts-Analyse aller LLMs
    st.subheader("⭐ Globale Qualitäts-Analyse")
    st.caption("Qualität aller getesteten LLMs über alle Server hinweg")
    
    # Qualitäts-Ranking aller LLMs
    quality_ranking = df.groupby('model').agg({
        'quality_avg': ['mean', 'max', 'min', 'count'],
        'performance': 'mean',
        'concurrent_efficiency': 'mean'
    }).round(3)
    
    # Flatten column names
    quality_ranking.columns = ['_'.join(col).strip() for col in quality_ranking.columns]
    quality_ranking = quality_ranking.reset_index()
    quality_ranking = quality_ranking.sort_values('quality_avg_mean', ascending=False)
    
    # Qualitäts-Chart - Ein Eintrag je Modell+Server
    df_quality = df.copy()
    df_quality['model_short'] = df_quality['model'].str.replace(':latest', '').str.replace(':12b', '').str.replace(':14b', '').str.replace(':8b', '')
    df_quality['server_short'] = df_quality['server'].str.replace('MacBook Pro ', 'MBP ').str.replace('localhost', 'Local')
    df_quality['display_name'] = df_quality['model_short'] + '<br>' + df_quality['server_short']
    
    fig_quality_global = px.bar(
        df_quality.sort_values('quality_avg', ascending=False),
        x='display_name',
        y='quality_avg',
        color='server',
        title='Qualität nach Modell und Server',
        labels={'quality_avg': 'Qualität', 'display_name': 'Modell + Server'},
        hover_data=['model', 'server', 'questions', 'concurrent']
    )
    fig_quality_global.update_layout(
        height=500,
        xaxis_title="Modell + Server",
        showlegend=True,
        legend=dict(title="Server")
    )
    st.plotly_chart(fig_quality_global, use_container_width=True)
    
    # Qualitäts-Ranking Tabelle
    st.dataframe(
        quality_ranking,
        use_container_width=True,
        hide_index=True,
        column_config={
            'model': st.column_config.TextColumn('Modell'),
            'quality_avg_mean': st.column_config.NumberColumn('Ø Qualität', format="%.3f"),
            'quality_avg_max': st.column_config.NumberColumn('Max Qualität', format="%.3f"),
            'quality_avg_min': st.column_config.NumberColumn('Min Qualität', format="%.3f"),
            'quality_avg_count': st.column_config.NumberColumn('Tests'),
            'performance_mean': st.column_config.NumberColumn('Ø Performance (T/s)', format="%.2f"),
            'concurrent_efficiency_mean': st.column_config.NumberColumn('Ø Concurrent-Eff.', format="%.2f")
        }
    )
    
    # Download-Option
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Als CSV herunterladen",
        data=csv,
        file_name=f"llm_auswertung_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def show_logs(logs: List[Dict]):
    """Zeigt Log-Analyse"""
    col_header, col_spacer, col_delete = st.columns([2, 1, 1])
    
    with col_header:
        st.header("📝 Log-Analyse")
    
    with col_delete:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacer für Alignment
        if st.button("🗑️ Logs löschen", help="Alle Log-Dateien löschen"):
            st.session_state.show_delete_logs_dialog = True
    
    # Dialog für Log-Löschung
    if st.session_state.get('show_delete_logs_dialog', False):
        st.warning("⚠️ **Möchten Sie wirklich alle Log-Dateien löschen?** Diese Aktion kann nicht rückgängig gemacht werden.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Ja, löschen"):
                import glob
                import os
                try:
                    log_files = glob.glob("logs/llm_stresstest_*.log")
                    deleted_count = 0
                    for log_file in log_files:
                        try:
                            os.remove(log_file)
                            deleted_count += 1
                        except Exception as e:
                            st.error(f"Fehler beim Löschen von {log_file}: {e}")
                    
                    if deleted_count > 0:
                        st.success(f"✅ {deleted_count} Log-Dateien wurden gelöscht!")
                        del st.session_state.show_delete_logs_dialog
                        st.rerun()
                    else:
                        st.info("Keine Log-Dateien zum Löschen gefunden.")
                except Exception as e:
                    st.error(f"Fehler beim Löschen der Logs: {e}")
        
        with col2:
            if st.button("❌ Abbrechen"):
                del st.session_state.show_delete_logs_dialog
                st.rerun()
        
        st.markdown("---")
    
    if not logs:
        st.warning("Keine Log-Dateien gefunden!")
        return
    
    log_df = pd.DataFrame(logs)
    
    # Filter
    col1, col2, col3 = st.columns(3)
    
    with col1:
        module_filter = st.selectbox(
            "Modul filtern:",
            ["Alle"] + list(log_df['module'].unique())
        )
    
    with col2:
        # Setze "Alle" als Standard
        unique_levels = ["Alle"] + list(log_df['level'].unique())
        default_index = 0
        
        level_filter = st.selectbox(
            "Log-Level:",
            unique_levels,
            index=default_index
        )
    
    with col3:
        search = st.text_input("Suche in Nachrichten:")
    
    # Filtering anwenden
    filtered_df = log_df.copy()
    
    if module_filter != "Alle":
        filtered_df = filtered_df[filtered_df['module'] == module_filter]
    
    if level_filter != "Alle":
        filtered_df = filtered_df[filtered_df['level'] == level_filter]
    
    if search:
        filtered_df = filtered_df[filtered_df['message'].str.contains(search, case=False, na=False)]
    
    # Fehler hervorheben
    errors = filtered_df[filtered_df['level'] == 'ERROR']
    warnings = filtered_df[filtered_df['level'] == 'WARNING']
    
    # Statistiken
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Gesamt Logs", len(filtered_df))
    with col2:
        st.metric("❌ Fehler", len(errors), delta_color="inverse")
    with col3:
        st.metric("⚠️ Warnungen", len(warnings), delta_color="inverse")
    with col4:
        st.metric("📁 Log-Dateien", log_df['file'].nunique())
    
    
    # Log-Tabelle mit horizontalem Scrollbalken
    col_log_title, col_refresh = st.columns([3, 1])
    
    with col_log_title:
        st.markdown("### 📋 Log-Einträge")
    
    with col_refresh:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacer für Alignment
        if st.button("🔄 Aktualisieren", help="Logs neu laden", key="refresh_logs_btn"):
            # Lösche Log-Cache um Neu-Einlesen zu erzwingen
            if 'log_cache' in st.session_state:
                del st.session_state.log_cache
            st.rerun()
    
    # Sortiere nach Timestamp (neueste zuerst) und begrenze auf 200 Einträge
    display_df = filtered_df.sort_values('timestamp', ascending=False).head(200).copy()
    
    if len(display_df) == 0:
        st.info("Keine Log-Einträge entsprechen den aktuellen Filtern.")
        return
    
    # Zeige DataFrame-Alternative mit besserer Nachricht-Anzeige
    # Kürze sehr lange Nachrichten für bessere Performance, aber zeige sie trotzdem vollständig
    display_df_clean = display_df.copy()
    
    # Füge Level-Emojis hinzu für bessere Unterscheidung
    level_emojis = {
        'ERROR': '🔴',
        'WARNING': '🟡', 
        'INFO': '🔵',
        'DEBUG': '🟣'
    }
    display_df_clean['level_display'] = display_df_clean['level'].map(lambda x: f"{level_emojis.get(x, '⚪')} {x}")
    
    # Zeige als Data Editor (erlaubt bessere Darstellung)
    st.data_editor(
        display_df_clean[['timestamp', 'module', 'level_display', 'message']],
        use_container_width=True,
        hide_index=True,
        height=600,
        disabled=True,  # Nicht editierbar
        column_config={
            "timestamp": st.column_config.TextColumn("🕒 Zeitstempel", width=180),
            "module": st.column_config.TextColumn("📦 Modul", width=120),
            "level_display": st.column_config.TextColumn("⚠️ Level", width=120),
            "message": st.column_config.TextColumn("💬 Nachricht", width=600)
        }
    )


def show_performance(df: pd.DataFrame, results: List[Dict]):
    """Zeigt Performance-Analyse"""
    st.header("⚡ Performance-Analyse")
    
    # Filter-Status anzeigen
    if 'filters_active' in st.session_state and st.session_state.get('filters_active', False):
        active_filters = st.session_state.get('active_filters', [])
        filter_text = " | ".join(active_filters) if active_filters else "unbekannt"
        st.warning(f"🔍 **Filter sind aktiv** ({filter_text}) - Nur gefilterte Modelle werden in der Analyse berücksichtigt!")
    
    # Hauptperformance-Ranking (wie bei Qualität)
    st.subheader("🏆 Performance-Ranking")
    st.caption("Performance aller getesteten LLMs nach Modell und Server")
    
    # Performance-Chart - Ein Eintrag je Modell+Server
    df_perf = df.copy()
    df_perf['model_short'] = df_perf['model'].str.replace(':latest', '').str.replace(':12b', '').str.replace(':14b', '').str.replace(':8b', '')
    df_perf['server_short'] = df_perf['server'].str.replace('MacBook Pro ', 'MBP ').str.replace('localhost', 'Local')
    df_perf['display_name'] = df_perf['model_short'] + '<br>' + df_perf['server_short']
    
    fig_perf_main = px.bar(
        df_perf.sort_values('performance', ascending=False),
        x='display_name',
        y='performance',
        color='server',
        title='Performance nach Modell und Server',
        labels={'performance': 'Performance (T/s)', 'display_name': 'Modell + Server'},
        hover_data=['model', 'server', 'questions', 'concurrent', 'runtime_avg', 'token_avg']
    )
    fig_perf_main.update_layout(
        height=500,
        xaxis_title="Modell + Server",
        showlegend=True,
        legend=dict(title="Server")
    )
    st.plotly_chart(fig_perf_main, use_container_width=True)
    
    # Performance-Details Tabelle
    st.subheader("📋 Performance-Details")
    detail_cols = ['model', 'server', 'questions', 'concurrent', 'performance', 'runtime_avg', 'token_avg', 'concurrent_efficiency', 'throughput_per_min']
    detail_df = df[detail_cols].copy().sort_values('performance', ascending=False)
    
    st.dataframe(
        detail_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'model': st.column_config.TextColumn('Modell'),
            'server': st.column_config.TextColumn('Server'),
            'questions': st.column_config.NumberColumn('Fragen'),
            'concurrent': st.column_config.NumberColumn('Parallel'),
            'performance': st.column_config.NumberColumn('Performance (T/s)', format="%.2f"),
            'runtime_avg': st.column_config.NumberColumn('Ø Zeit (ms)', format="%.1f"),
            'token_avg': st.column_config.NumberColumn('Ø Tokens'),
            'concurrent_efficiency': st.column_config.NumberColumn('Concurrent-Eff.', format="%.2f"),
            'throughput_per_min': st.column_config.NumberColumn('Durchsatz (/min)', format="%.2f")
        }
    )
    
    st.markdown("---")
    
    # LLM Load Time Analyse (separate Sektion)
    st.subheader("🚀 LLM Load Time Analyse")
    st.caption("Startup-Performance und Cold Start Faktoren")
    
    if df['llm_load_time'].sum() > 0:
        load_time_df = df[df['llm_load_time'] > 0].copy()
        
        # Metriken
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_load_time = load_time_df['llm_load_time'].mean()
            st.metric("Ø Ladezeit", f"{avg_load_time:.1f} ms")
        
        with col2:
            max_load_time = load_time_df['llm_load_time'].max()
            st.metric("Max Ladezeit", f"{max_load_time:.1f} ms")
        
        with col3:
            avg_cold_start = load_time_df['cold_start_factor'].mean()
            st.metric("Ø Cold Start Faktor", f"{avg_cold_start:.2f}x")
        
        with col4:
            avg_load_eff = load_time_df['load_efficiency'].mean()
            st.metric("Ø Load-Effizienz (%)", f"{avg_load_eff:.1f}")
        
        # Load Time vs Runtime Vergleich
        col1, col2 = st.columns(2)
        
        with col1:
            # Load Time Balkendiagramm
            load_time_df['display_name'] = load_time_df['model'].str.replace(':latest', '').str.replace(':12b', '').str.replace(':14b', '').str.replace(':8b', '') + '<br>(' + load_time_df['server'].str.replace('MacBook Pro ', 'MBP ') + ')'
            
            fig_load_time = px.bar(
                load_time_df.sort_values('llm_load_time', ascending=False),
                x='display_name',
                y='llm_load_time',
                color='server',
                title='LLM Ladezeit Ranking',
                labels={'llm_load_time': 'Ladezeit (ms)', 'display_name': 'Modell + Server'}
            )
            fig_load_time.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_load_time, use_container_width=True)
        
        with col2:
            # Load Time vs Runtime Scatter
            fig_load_scatter = px.scatter(
                load_time_df,
                x='runtime_avg',
                y='llm_load_time',
                color='model',
                size='performance',
                hover_data=['server', 'cold_start_factor'],
                title='Load Time vs. Runtime',
                labels={'runtime_avg': 'Ø Runtime (ms)', 'llm_load_time': 'Load Time (ms)'}
            )
            fig_load_scatter.update_layout(height=400)
            st.plotly_chart(fig_load_scatter, use_container_width=True)
    else:
        st.info("Keine Load Time Daten verfügbar. Führe Tests mit der aktuellen Version durch.")
    
    st.markdown("---")
    
    # Effizienz-Empfehlungen
    st.subheader("💡 Performance-Empfehlungen")
    
    if not df.empty:
        # Beste Performance
        best_perf = df.loc[df['performance'].idxmax()]
        
        # Bester Durchsatz
        best_throughput = df.loc[df['throughput_per_min'].idxmax()]
        
        # Beste Load Time (wenn verfügbar)
        if df['llm_load_time'].sum() > 0:
            best_load = df[df['llm_load_time'] > 0].loc[df[df['llm_load_time'] > 0]['llm_load_time'].idxmin()]
        else:
            best_load = None
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.success(f"""
            **🏆 Höchste Performance**
            - **Modell**: {best_perf['model']}
            - **Server**: {best_perf['server']}
            - **Performance**: {best_perf['performance']:.2f} T/s
            - **Empfehlung**: Für maximale Token/s
            """)
        
        with col2:
            st.info(f"""
            **⚡ Bester Durchsatz**
            - **Modell**: {best_throughput['model']}
            - **Server**: {best_throughput['server']}
            - **Durchsatz**: {best_throughput['throughput_per_min']:.1f} /min
            - **Empfehlung**: Für viele kurze Anfragen
            """)
        
        with col3:
            if best_load is not None:
                st.warning(f"""
                **🚀 Schnellster Start**
                - **Modell**: {best_load['model']}
                - **Server**: {best_load['server']}
                - **Load Time**: {best_load['llm_load_time']:.1f} ms
                - **Empfehlung**: Für schnelle Initialisierung
                """)
            else:
                st.info("**Load Time Daten**\n\nKeine Daten verfügbar. Führe Tests mit aktueller Version durch.")
    
    
    # Efficiency Matrix
    st.subheader("🎯 Effizienz-Matrix")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Quality vs Performance
        fig_efficiency = px.scatter(
            df,
            x='performance',
            y='quality_avg',
            color='model',
            size='questions',
            hover_data=['server'],
            title='Qualität vs. Performance',
            labels={'performance': 'Performance (T/s)', 'quality_avg': 'Durchschnittliche Qualität'}
        )
        st.plotly_chart(fig_efficiency, use_container_width=True)
    
    with col2:
        # Time Distribution
        time_data = []
        for result in results:
            for item in result.get('results', []):
                time_data.append({
                    'model': result['meta'].get('model', 'Unknown'),
                    'time': item.get('time', 0)
                })
        
        if time_data:
            time_df = pd.DataFrame(time_data)
            
            # Statistiken berechnen
            time_stats = time_df.groupby('model')['time'].agg([
                'mean', 'median', 'std', 'min', 'max', 'count'
            ]).round(1)
            
            # Anzeigeart auswählen
            chart_type = st.selectbox(
                "Anzeigeart wählen:",
                ["Balkendiagramm (Durchschnitt)", "Violin-Plot", "Histogram", "Statistik-Tabelle"],
                index=0
            )
            
            if chart_type == "Balkendiagramm (Durchschnitt)":
                fig = px.bar(
                    time_stats.reset_index(),
                    x='model',
                    y='mean',
                    title='Durchschnittliche Antwortzeit nach Modell',
                    labels={'mean': 'Ø Zeit (ms)', 'model': 'Modell'},
                    text='mean'
                )
                fig.update_traces(texttemplate='%{text:.1f}ms', textposition='outside')
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
                
            elif chart_type == "Violin-Plot":
                fig = px.violin(
                    time_df,
                    x='model',
                    y='time',
                    title='Zeitverteilung nach Modell (Violin-Plot)',
                    labels={'time': 'Zeit (ms)', 'model': 'Modell'},
                    box=True
                )
                st.plotly_chart(fig, use_container_width=True)
                
            elif chart_type == "Histogram":
                selected_models = st.multiselect(
                    "Modelle für Vergleich auswählen:",
                    time_df['model'].unique(),
                    default=time_df['model'].unique()[:3]
                )
                
                filtered_data = time_df[time_df['model'].isin(selected_models)]
                fig = px.histogram(
                    filtered_data,
                    x='time',
                    color='model',
                    title='Zeitverteilung Histogram',
                    labels={'time': 'Zeit (ms)', 'count': 'Anzahl'},
                    marginal='box',
                    opacity=0.7
                )
                st.plotly_chart(fig, use_container_width=True)
                
            elif chart_type == "Statistik-Tabelle":
                st.subheader("📊 Detaillierte Zeitstatistiken")
                st.dataframe(
                    time_stats,
                    use_container_width=True,
                    column_config={
                        'mean': st.column_config.NumberColumn('Durchschnitt (ms)', format="%.1f"),
                        'median': st.column_config.NumberColumn('Median (ms)', format="%.1f"),
                        'std': st.column_config.NumberColumn('Standardabw. (ms)', format="%.1f"),
                        'min': st.column_config.NumberColumn('Minimum (ms)', format="%.1f"),
                        'max': st.column_config.NumberColumn('Maximum (ms)', format="%.1f"),
                        'count': st.column_config.NumberColumn('Anzahl Tests')
                    }
                )


def show_comparisons(df: pd.DataFrame, results: List[Dict]):
    """Zeigt Vergleichsanalysen"""
    st.header("🔄 Modell- und Server-Vergleiche")
    
    # Filter-Status anzeigen
    if 'filters_active' in st.session_state and st.session_state.get('filters_active', False):
        active_filters = st.session_state.get('active_filters', [])
        filter_text = " | ".join(active_filters) if active_filters else "unbekannt"
        st.warning(f"🔍 **Filter sind aktiv** ({filter_text}) - Nur gefilterte Modelle werden in den Vergleichen berücksichtigt!")
    
    # Hinweis auf Normalisierung
    st.info("""
    📊 **Alle Vergleiche verwenden normalisierte Metriken** für faire Bewertung trotz unterschiedlicher Test-Konfigurationen.
    """)
    
    # Vergleichstyp auswählen
    comparison_type = st.radio(
        "Vergleichstyp wählen:",
        ["Gleiche Modelle, verschiedene Server", "Gleicher Server, verschiedene Modelle"]
    )
    
    if comparison_type == "Gleiche Modelle, verschiedene Server":
        # Modell auswählen
        models = df['model'].unique()
        selected_model = st.selectbox("Modell auswählen:", models)
        
        # Daten filtern
        model_df = df[df['model'] == selected_model]
        
        if len(model_df) > 1:
            # Vergleichsgrafiken
            col1, col2 = st.columns(2)
            
            with col1:
                # Performance-Vergleich
                fig_perf = px.bar(
                    model_df,
                    x='server',
                    y='performance',
                    title=f'Performance-Vergleich: {selected_model}',
                    labels={'performance': 'Tokens/Sekunde', 'server': 'Server'}
                )
                st.plotly_chart(fig_perf, use_container_width=True)
            
            with col2:
                # Qualitäts-Vergleich
                fig_quality = px.bar(
                    model_df,
                    x='server',
                    y='quality_avg',
                    title=f'Qualitäts-Vergleich: {selected_model}',
                    labels={'quality_avg': 'Durchschnittliche Qualität', 'server': 'Server'}
                )
                st.plotly_chart(fig_quality, use_container_width=True)
            
            # Detailtabelle mit normalisierten Metriken
            st.subheader(f"📋 Details für {selected_model}")
            detail_cols = ['server', 'questions', 'concurrent', 'runtime_avg', 'performance', 'concurrent_efficiency', 'throughput_per_min', 'quality_avg']
            st.dataframe(
                model_df[detail_cols],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info(f"Nur ein Server für Modell {selected_model} gefunden.")
    
    else:  # Gleicher Server, verschiedene Modelle
        # Server auswählen
        servers = df['server'].unique()
        selected_server = st.selectbox("Server auswählen:", servers)
        
        # Daten filtern
        server_df = df[df['server'] == selected_server]
        
        if len(server_df) > 1:
            # Balkengrafik mit allen Modellen
            st.subheader(f"📊 Modell-Vergleich auf {selected_server}")
            
            # Multi-Metrik Balkendiagramm mit normalisierten Metriken
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Performance (T/s)', 'Concurrent-Effizienz',
                               'Durchsatz (/min)', 'Qualität (normalisiert)')
            )
            
            # Performance
            fig.add_trace(
                go.Bar(x=server_df['model'], y=server_df['performance'], name='Performance'),
                row=1, col=1
            )
            
            # Concurrent Efficiency
            fig.add_trace(
                go.Bar(x=server_df['model'], y=server_df['concurrent_efficiency'], name='Concurrent Eff.'),
                row=1, col=2
            )
            
            # Throughput
            fig.add_trace(
                go.Bar(x=server_df['model'], y=server_df['throughput_per_min'], name='Durchsatz'),
                row=2, col=1
            )
            
            # Quality (normalized)
            fig.add_trace(
                go.Bar(x=server_df['model'], y=server_df['quality_normalized'], name='Quality'),
                row=2, col=2
            )
            
            fig.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Ranking-Tabelle mit normalisierten Metriken
            st.subheader("🏆 Modell-Ranking (normalisiert)")
            ranking_cols = ['model', 'questions', 'concurrent', 'performance', 'concurrent_efficiency', 'throughput_per_min', 'quality_normalized']
            ranking_df = server_df[ranking_cols].copy()
            ranking_df = ranking_df.sort_values('performance', ascending=False)
            
            st.dataframe(
                ranking_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'model': st.column_config.TextColumn('Modell'),
                    'runtime_avg': st.column_config.NumberColumn('Ø Zeit (ms)', format="%.1f"),
                    'token_avg': st.column_config.NumberColumn('Ø Tokens'),
                    'quality_avg': st.column_config.NumberColumn('Ø Qualität', format="%.3f"),
                    'performance': st.column_config.NumberColumn('Performance (T/s)', format="%.2f")
                }
            )
        else:
            st.info(f"Nur ein Modell auf Server {selected_server} gefunden.")


def show_quality_metrics(analyzer: LLMAnalyzer, results: List[Dict]):
    """Zeigt detaillierte Qualitätsmetriken"""
    st.header("📈 Qualitätsmetriken-Analyse")
    
    # Filter-Status anzeigen  
    if 'filters_active' in st.session_state and st.session_state.get('filters_active', False):
        active_filters = st.session_state.get('active_filters', [])
        filter_text = " | ".join(active_filters) if active_filters else "unbekannt"
        st.warning(f"🔍 **Filter sind aktiv** ({filter_text}) - Nur gefilterte Modelle werden in der Qualitätsanalyse berücksichtigt!")
    
    # Lade detaillierte Qualitätsmetriken
    quality_df = analyzer.get_detailed_quality_metrics()
    
    if quality_df.empty:
        st.warning("Keine Qualitätsmetriken in den Daten gefunden!")
        st.info("Führe Tests mit der neuesten Version durch, um Qualitätsmetriken zu erhalten.")
        return
    
    # Modell auswählen für Details
    models = quality_df['model'].unique()
    selected_models = st.multiselect(
        "Modelle für Vergleich auswählen:",
        models,
        default=models[:3] if len(models) >= 3 else models
    )
    
    if selected_models:
        filtered_quality = quality_df[quality_df['model'].isin(selected_models)]
        
        # Metriken für Radar-Chart
        metrics = ['structure_score', 'readability_score', 'completeness_score', 
                  'relevance_score', 'factual_consistency', 'fluency_score', 'coherence_score']
        
        # Durchschnittswerte berechnen
        avg_metrics = filtered_quality.groupby('model')[metrics].mean()
        
        # Gesamtqualität Balkendiagramm
        st.subheader("🎯 Gesamtqualität nach Modell")
        
        # Berechne Gesamtqualität als Durchschnitt aller Metriken
        overall_quality = filtered_quality.groupby('model')[metrics].mean()
        overall_quality['overall_avg'] = overall_quality.mean(axis=1)
        overall_quality_sorted = overall_quality.reset_index().sort_values('overall_avg', ascending=False)
        
        fig_overall = px.bar(
            overall_quality_sorted,
            x='model',
            y='overall_avg',
            title='Gesamtqualität - Durchschnitt aller Metriken',
            labels={'model': 'Modell', 'overall_avg': 'Gesamtqualität'},
            color='overall_avg',
            color_continuous_scale='RdYlGn'
        )
        fig_overall.update_layout(height=400)
        st.plotly_chart(fig_overall, use_container_width=True)
        
        # Detaillierte Metrik-Tabelle
        st.subheader("📊 Durchschnittliche Qualitätsmetriken")
        
        display_metrics = avg_metrics.round(3)
        display_metrics['overall_avg'] = display_metrics.mean(axis=1).round(3)
        
        st.dataframe(
            display_metrics,
            use_container_width=True,
            column_config={
                'structure_score': st.column_config.NumberColumn('Struktur', format="%.3f"),
                'readability_score': st.column_config.NumberColumn('Lesbarkeit', format="%.3f"),
                'completeness_score': st.column_config.NumberColumn('Vollständigkeit', format="%.3f"),
                'relevance_score': st.column_config.NumberColumn('Relevanz', format="%.3f"),
                'factual_consistency': st.column_config.NumberColumn('Faktische Konsistenz', format="%.3f"),
                'fluency_score': st.column_config.NumberColumn('Sprachfluss', format="%.3f"),
                'coherence_score': st.column_config.NumberColumn('Kohärenz', format="%.3f"),
                'overall_avg': st.column_config.NumberColumn('Gesamt Ø', format="%.3f")
            }
        )
        
        # Balkendiagramm für einzelne Metriken
        st.subheader("📈 Metrik-Verteilungen")
        
        selected_metric = st.selectbox(
            "Metrik für Detailansicht:",
            metrics,
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        # Metrik-Beschreibungen
        metric_descriptions = {
            'structure_score': {
                'name': 'Struktur-Score',
                'description': """**Was es misst:** Strukturelle Organisation und Formatierung der Antwort
- Verwendung von Absätzen, Listen, Aufzählungen
- Hervorhebungen (fett, kursiv)
- Angemessene Textlänge (50-1000 Wörter ideal)
- Verwendung von Beispielen"""
            },
            'readability_score': {
                'name': 'Lesbarkeits-Score',
                'description': """**Was es misst:** Wie leicht verständlich der Text ist
- Durchschnittliche Satzlänge (15-20 Wörter ideal)
- Durchschnittliche Wortlänge (4-6 Zeichen ideal)
- Komplexität der Sprache"""
            },
            'completeness_score': {
                'name': 'Vollständigkeits-Score',
                'description': """**Was es misst:** Wie vollständig die Frage beantwortet wird
- Mindestlänge erreicht (30+ Wörter)
- Bezug zu Schlüsselwörtern der Frage
- Hat Einleitung/Erklärung
- Hat Abschluss/Zusammenfassung"""
            },
            'relevance_score': {
                'name': 'Relevanz-Score',
                'description': """**Was es misst:** Wie gut die Antwort zur gestellten Frage passt
- Semantische Ähnlichkeit zwischen Frage und Antwort
- Verwendung relevanter Schlüsselwörter
- Thematischer Bezug"""
            },
            'factual_consistency': {
                'name': 'Faktische Konsistenz',
                'description': """**Was es misst:** Widerspruchsfreiheit innerhalb der Antwort
- Keine sich widersprechenden Aussagen
- Konsistente Zahlenangaben
- Keine logischen Brüche"""
            },
            'fluency_score': {
                'name': 'Sprachfluss-Score',
                'description': """**Was es misst:** Sprachliche Qualität und Natürlichkeit
- Grammatikalische Korrektheit
- Natürlicher Sprachfluss
- Abwechslungsreiche Satzstrukturen
- Verwendung von Verbindungswörtern"""
            },
            'coherence_score': {
                'name': 'Kohärenz-Score',
                'description': """**Was es misst:** Logischer Zusammenhang und Gedankenführung
- Verwendung von Verbindungswörtern (deshalb, außerdem, jedoch)
- Thematische Konsistenz durch wiederkehrende Begriffe
- Erkennbare Struktur/Progression"""
            }
        }
        
        # Beschreibung der gewählten Metrik anzeigen
        if selected_metric in metric_descriptions:
            metric_info = metric_descriptions[selected_metric]
            st.info(f"#### {metric_info['name']}\n{metric_info['description']}")
        
        st.markdown("---")
        
        # Durchschnittswerte für die ausgewählte Metrik
        metric_avg = filtered_quality.groupby('model')[selected_metric].mean().reset_index()
        metric_avg = metric_avg.sort_values(selected_metric, ascending=False)
        
        fig_bar = px.bar(
            metric_avg,
            x='model',
            y=selected_metric,
            title=f'{selected_metric.replace("_", " ").title()} - Durchschnittswerte',
            labels={'model': 'Modell', selected_metric: 'Score'},
            color=selected_metric,
            color_continuous_scale='RdYlGn'
        )
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Zusätzliche Statistiken
        col1, col2, col3 = st.columns(3)
        
        with col1:
            best_model = avg_metrics['overall_avg'].idxmax() if 'overall_avg' in avg_metrics.columns else avg_metrics.mean(axis=1).idxmax()
            st.metric("🏆 Bestes Modell (Qualität)", best_model)
        
        with col2:
            avg_quality_all = filtered_quality['overall_quality'].mean()
            st.metric("Ø Gesamtqualität", f"{avg_quality_all:.3f}")
        
        with col3:
            consistency = filtered_quality.groupby('model')['overall_quality'].std().mean()
            st.metric("Ø Konsistenz (Std)", f"{consistency:.3f}", delta_color="inverse")


def show_configuration(results: List[Dict]):
    """Zeigt Stresstest-Konfiguration und Start-Seite"""
    
    # Drei-Spalten-Layout mit Abstand
    col1, col_spacer, col2 = st.columns([2, 0.5, 1.5])
    
    with col1:
        st.subheader("🔧 Server & Model")
        
        # Config laden
        config_path = Path("config/config.json")
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except:
            config = {
                "questions": 10,
                "concurrent": 2,
                "url": "http://localhost:11434",
                "server_name": "localhost",
                "model": "llama2",
                "timeout": 120.0,
                "max_keepalive_connections": 20
            }
        
        # Server-Historie aus Results extrahieren
        server_history = {}
        for result in results:
            if 'meta' in result:
                server_name = result['meta'].get('server_name', '')
                server_url = result['meta'].get('server', '')
                if server_name and server_url:
                    server_history[server_name] = server_url
        
        # Server-Auswahl
        st.markdown("**Server-Konfiguration:**")
        server_options = ["[Neuer Server]"] + sorted(server_history.keys())
        selected_server_option = st.selectbox(
            "Server auswählen:",
            server_options,
            index=0 if config.get('server_name') not in server_history else server_options.index(config.get('server_name')),
            key="config_server_select"
        )
        
        # URL-Validierungsfunktion
        def validate_url(url):
            """Validiert und bereinigt Server-URLs"""
            from urllib.parse import urlparse
            
            # Bereinige Whitespace
            url = url.strip()
            
            # Prüfe auf gefährliche Zeichen
            if any(char in url for char in [';', '`', '$', '|', '>', '<', '&', '\n', '\r']):
                return None, "❌ URL enthält ungültige Zeichen"
            
            # Parse URL
            try:
                parsed = urlparse(url)
                # Erlaube nur http und https
                if parsed.scheme not in ['http', 'https']:
                    return None, "❌ Nur http:// oder https:// URLs erlaubt"
                # Prüfe auf gültigen Host
                if not parsed.hostname:
                    return None, "❌ Kein gültiger Hostname in der URL"
                # Blocke gefährliche Hosts
                blocked_hosts = ['0.0.0.0', '255.255.255.255']
                if parsed.hostname in blocked_hosts:
                    return None, "❌ Diese Host-Adresse ist nicht erlaubt"
                return url, None
            except Exception as e:
                return None, f"❌ Ungültige URL: {str(e)}"
        
        if selected_server_option == "[Neuer Server]":
            server_name = st.text_input(
                "Server-Name:",
                value=config.get('server_name', 'localhost'),
                key="config_server_name_input",
                max_chars=50,  # Begrenze Länge
                help="Eindeutiger Name für diesen Server (max. 50 Zeichen)"
            )
            server_url_input = st.text_input(
                "Server-URL:",
                value=config.get('url', 'http://localhost:11434'),
                key="config_server_url_input",
                max_chars=200,  # Begrenze Länge
                help="URL des LLM-Servers (z.B. http://localhost:11434)"
            )
            # Validiere URL
            server_url, url_error = validate_url(server_url_input)
            if url_error:
                st.error(url_error)
                server_url = None  # Verhindere Speicherung ungültiger URLs
            else:
                server_url = server_url_input
        else:
            server_name = selected_server_option
            server_url = server_history[selected_server_option]
            st.info(f"**URL:** {server_url}")
        
        # Model-Auswahl (ohne Überschrift)
        
        # Versuche verfügbare Modelle von API zu laden
        available_models = []
        if st.button("🔄 Modelle laden", key="config_load_models_btn", help="Verfügbare Modelle von API laden"):
            models_found = False
            
            with st.spinner("Lade verfügbare Modelle..."):
                # 1. Versuche Ollama API (/api/tags)
                try:
                    api_url = f"{server_url}/api/tags"
                    response = requests.get(api_url, timeout=5)
                    if response.status_code == 200:
                        models_data = response.json()
                        if 'models' in models_data:
                            available_models = [m['name'] for m in models_data['models']]
                            models_found = True
                except Exception as e:
                    pass  # Versuche nächste API
                
                # 2. Versuche OpenAI-kompatible API (/v1/models)
                if not models_found:
                    try:
                        api_url = f"{server_url}/v1/models"
                        response = requests.get(api_url, timeout=5)
                        if response.status_code == 200:
                            models_data = response.json()
                            if 'data' in models_data:
                                available_models = [m['id'] for m in models_data['data']]
                                models_found = True
                    except Exception as e:
                        pass  # Versuche nächste API
                
                # 3. Versuche LM Studio API (/models)
                if not models_found:
                    try:
                        api_url = f"{server_url}/models"
                        response = requests.get(api_url, timeout=5)
                        if response.status_code == 200:
                            models_data = response.json()
                            if isinstance(models_data, list):
                                available_models = [m.get('id', m.get('name', str(m))) for m in models_data if isinstance(m, dict)]
                            elif isinstance(models_data, dict) and 'models' in models_data:
                                available_models = [m.get('id', m.get('name', str(m))) for m in models_data['models']]
                            if available_models:
                                models_found = True
                    except Exception as e:
                        pass
                
                # 4. Fallback: Direkter API-Test mit /api/chat
                if not models_found:
                    try:
                        # Test ob Server überhaupt erreichbar ist
                        test_url = f"{server_url}/api/chat"
                        response = requests.post(test_url, json={"model": "test", "messages": []}, timeout=2)
                        if response.status_code in [200, 400, 422]:  # 400/422 = Server antwortet, aber falsches Format
                            st.info("🔍 Server erreichbar, aber keine Modell-Liste verfügbar")
                            st.info("💡 Bitte Model manuell eingeben")
                        else:
                            st.warning("⚠️ Server antwortet nicht auf API-Anfragen")
                    except Exception as e:
                        st.error(f"❌ Server nicht erreichbar: {type(e).__name__}")
                
                # Session State für persistente Model-Liste
                if available_models:
                    st.session_state.config_available_models = available_models
        
        # Model-Eingabe - verwende Session State für Persistenz
        session_models = st.session_state.get('config_available_models', [])
        combined_models = list(set(available_models + session_models))  # Kombiniere aktuelle und gespeicherte Modelle
        
        if combined_models:
            # Zeige gefundene Modelle in Selectbox
            model_input = st.selectbox(
                "Model:",
                combined_models,
                index=combined_models.index(config.get('model')) if config.get('model') in combined_models else 0,
                key="config_model_select"
            )
            # Zusätzliche manuelle Eingabe für andere Modelle
            manual_model = st.text_input(
                "Oder Model manuell eingeben:",
                value="",
                key="config_model_manual",
                help="Lässt das obige Dropdown außer Acht"
            )
            if manual_model.strip():
                model_input = manual_model.strip()
        else:
            # Fallback: Nur manuelle Eingabe
            model_input = st.text_input(
                "Model (manuell eingeben):",
                value=config.get('model', 'qwen2.5:14b'),
                key="config_model_input"
            )
    
    with col2:
        st.subheader("📊 Test-Parameter")
        
        # Sicherheitslimits für Parameter
        questions = st.number_input(
            "Anzahl Fragen:",
            min_value=1,
            max_value=100,  # Reduziert von 234 auf 100 für Sicherheit
            value=min(config.get('questions', 10), 100),
            key="config_questions_input",
            help="⚠️ Max. 100 Fragen für Serverschutz (Pool: 234 verfügbar)"
        )
        
        concurrent = st.number_input(
            "Parallele Anfragen:",
            min_value=1,
            max_value=20,  # Reduziert von 50 auf 20 für Sicherheit
            value=min(config.get('concurrent', 2), 20),
            key="config_concurrent_input",
            help="⚠️ Max. 20 parallele Anfragen zum Schutz des Servers"
        )
        
        timeout = st.number_input(
            "Timeout (Sekunden):",
            min_value=10.0,
            max_value=300.0,  # Reduziert von 600 auf 300 (5 Min)
            value=min(config.get('timeout', 120.0), 300.0),
            step=10.0,
            key="config_timeout_input",
            help="⚠️ Max. 300 Sekunden (5 Min) Timeout"
        )
        
        max_keepalive = st.number_input(
            "Max Keepalive Connections:",
            min_value=1,
            max_value=50,  # Reduziert von 100 auf 50
            value=min(config.get('max_keepalive_connections', 20), 50),
            key="config_keepalive_input",
            help="⚠️ Max. 50 persistente Verbindungen"
        )
        
        # Sicherheitswarnung bei hohen Werten
        if questions > 50 or concurrent > 10:
            st.warning("⚠️ **Achtung:** Hohe Werte können den Server überlasten!")
        
        # Config speichern
        new_config = {
            "questions": questions,
            "concurrent": concurrent,
            "url": server_url,
            "server_name": server_name,
            "model": model_input,
            "timeout": timeout,
            "max_keepalive_connections": max_keepalive
        }
        
        # Automatisch speichern wenn sich was ändert
        if new_config != config:
            try:
                with open(config_path, 'w') as f:
                    json.dump(new_config, f, indent=4)
                st.success("✅ Konfiguration gespeichert")
            except Exception as e:
                st.error(f"❌ Fehler beim Speichern: {str(e)}")
    
    # Stresstest-Start Bereich
    st.markdown("---")
    st.subheader("🚀 Stresstest starten")
    
    col_start = st.columns([1])[0]
    
    with col_start:
        if st.button("▶️ Stresstest starten", key="start_test_btn", help="Starte den konfigurierten Stresstest"):
            # Bestätige alle erforderlichen Parameter
            try:
                with open("config/config.json", "r") as f:
                    current_config = json.load(f)
            except Exception as e:
                st.error(f"❌ Fehler beim Laden der Konfiguration: {e}")
                return
            
            # Prüfe Dateienanme für mögliche Überschreibung
            server_name = current_config.get('server_name', 'unknown')
            model = current_config.get('model', 'unknown')
            
            # Dateiname generieren (gleiche Logik wie im Stresstest)
            def sanitize_filename(text: str) -> str:
                import re
                text = text.replace(' ', '-')
                text = re.sub(r'[^a-zA-Z0-9\\-]', '_', text)
                text = re.sub(r'[-_]+', lambda m: m.group(0)[0], text)
                return text.strip('-_')
            
            clean_server = sanitize_filename(server_name)
            clean_model = sanitize_filename(model)
            filename = f"result_{clean_server}_{clean_model}"
            result_path = Path('results') / f"{filename}.json"
            
            # Dialog bei existierender Datei
            if result_path.exists() and 'test_confirmed' not in st.session_state:
                st.warning(f"📊 **Für diese Konfiguration wurde bereits ein Test durchgeführt.**")
                st.info("Die Ergebnisdatei wird überschrieben.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Fortfahren", key="continue_test_btn"):
                        try:
                            result_path.unlink()
                            st.success("✅ Datei gelöscht - Test startet...")
                            st.session_state.test_confirmed = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Fehler: {e}")
                            return
                
                with col2:
                    if st.button("❌ Abbrechen", key="cancel_test_btn"):
                        st.info("Test abgebrochen")
                        return
                
                return
            
            # Lösche Flag nach Test-Start
            if 'test_confirmed' in st.session_state:
                del st.session_state.test_confirmed
                
            # Starte Stresstest
            st.success("🚀 Stresstest wird gestartet...")
            
            import subprocess
            import os
            
            try:
                # Starte llm_stresstest.py mit --force Parameter
                process = subprocess.Popen(
                    ["python", "llm_stresstest.py", "--force"], 
                    cwd=os.getcwd(),
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Warte auf Ende mit Spinner
                with st.spinner("🔄 Test läuft... Bitte warten"):
                    stdout, stderr = process.communicate()
                
                # Zeige Ergebnis
                if process.returncode == 0:
                    st.success("✅ Stresstest erfolgreich abgeschlossen!")
                    
                    # Zeige letzte Ausgabezeilen
                    if stdout:
                        lines = stdout.strip().split('\n')
                        recent_lines = lines[-5:] if len(lines) > 5 else lines
                        with st.expander("📄 Test-Ausgabe (letzte Zeilen)", expanded=False):
                            st.text('\n'.join(recent_lines))
                    
                    # Nach Erfolg zu Ergebnissen wechseln
                    import time
                    time.sleep(1)
                    st.session_state.current_page = "📊 Vergleiche" 
                    st.rerun()
                else:
                    st.error(f"❌ Stresstest fehlgeschlagen (Exit Code: {process.returncode})")
                    
                    if stderr:
                        st.error(f"**Fehlerdetails:**\n{stderr}")
                    
                    if stdout:
                        with st.expander("📄 Vollständige Ausgabe", expanded=False):
                            st.text(stdout)
            
            except Exception as e:
                st.error(f"❌ Fehler beim Starten des Stresstests: {str(e)}")
                st.code(str(e), language="python")



if __name__ == "__main__":
    main()