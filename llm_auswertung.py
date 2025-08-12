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
        self.log_path = Path('.')
        self.data = []
        self.logs = []
        
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
            
            row = {
                'filename': result['filename'],
                'server': meta.get('server_name', meta.get('server', 'Unknown')),  # Nutze server_name, fallback auf server/URL
                'server_url': meta.get('server', 'Unknown'),
                'model': meta.get('model', 'Unknown'),
                'questions': meta.get('questions', 0),
                'concurrent': meta.get('concurrent', 1),
                'total_duration_ms': meta.get('total_duration_ms', 0),
                'runtime_avg': aggregate.get('runtime_avg', 0),
                'token_avg': aggregate.get('token_avg', 0),
                'quality_avg': aggregate.get('quality_avg', 0),
                'llm_load_time': aggregate.get('llm_load_time', 0),
                'cold_start_factor': aggregate.get('cold_start_factor', 0),
                'start_time': meta.get('start_time', ''),
                'start_date': meta.get('start_date', '')
            }
            
            # Performance berechnen (Token/Zeit)
            if row['runtime_avg'] > 0:
                row['performance'] = round(row['token_avg'] / (row['runtime_avg'] / 1000), 2)
            else:
                row['performance'] = 0
            
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
    st.title("🔬 LLM Stresstest Auswertung Dashboard")
    st.markdown("---")
    
    # Analyzer initialisieren
    analyzer = LLMAnalyzer()
    
    # Elegante Sidebar Navigation
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: #1f77b4; margin-bottom: 30px;">🎛️ Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation mit custom styling
    nav_options = {
        "📊 Übersicht": {"icon": "📊", "desc": "Gesamtstatistiken & Übersicht"},
        "📝 Logs": {"icon": "📝", "desc": "Log-Analyse & Fehlersuche"},
        "⚡ Performance": {"icon": "⚡", "desc": "Performance & Ladezeiten"},
        "🔄 Vergleiche": {"icon": "🔄", "desc": "Server & Modell-Vergleiche"},
        "📈 Qualitätsmetriken": {"icon": "📈", "desc": "Detaillierte Qualitätsanalyse"}
    }
    
    # Custom Radio Buttons mit Beschreibungen
    selected_page = None
    for i, (page_name, info) in enumerate(nav_options.items()):
        if st.sidebar.button(
            f"{info['icon']} {page_name.split(' ', 1)[1]}",
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
        logs = analyzer.load_logs()
    
    if not results:
        st.error("❌ Keine Result-Dateien im ./results Verzeichnis gefunden!")
        st.info("Führe zuerst einen Stresstest aus: `python llm_stresstest.py <output_name>`")
        return
    
    df = analyzer.get_dataframe()
    
    # Sidebar Info
    st.sidebar.markdown("---")
    st.sidebar.info(f"📁 {len(results)} Result-Dateien geladen")
    st.sidebar.info(f"📝 {len(logs)} Log-Einträge gefunden")
    
    # Hauptinhalt basierend auf Auswahl
    if page == "📊 Übersicht":
        show_overview(df, results)
    elif page == "📝 Logs":
        show_logs(logs)
    elif page == "⚡ Performance":
        show_performance(df, results)
    elif page == "🔄 Vergleiche":
        show_comparisons(df, results)
    elif page == "📈 Qualitätsmetriken":
        show_quality_metrics(analyzer, results)


def show_overview(df: pd.DataFrame, results: List[Dict]):
    """Zeigt Übersichtsseite"""
    st.header("📊 Gesamtübersicht")
    
    # Metriken in Spalten
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tests durchgeführt", len(results))
    with col2:
        st.metric("Verschiedene Modelle", df['model'].nunique())
    with col3:
        st.metric("Verschiedene Server", df['server'].nunique())
    with col4:
        avg_quality = df['quality_avg'].mean()
        st.metric("Ø Qualität", f"{avg_quality:.3f}" if not pd.isna(avg_quality) else "N/A")
    
    st.markdown("---")
    
    # Übersichtstabelle
    st.subheader("📋 Alle Tests")
    
    # Spalten auswählen
    display_cols = ['filename', 'server', 'model', 'questions', 'runtime_avg', 'token_avg', 'quality_avg', 'performance']
    display_df = df[display_cols].copy()
    
    # Formatierung
    display_df['runtime_avg'] = display_df['runtime_avg'].round(1)
    display_df['quality_avg'] = display_df['quality_avg'].round(3)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'filename': st.column_config.TextColumn('Datei'),
            'server': st.column_config.TextColumn('Server'),
            'model': st.column_config.TextColumn('Modell'),
            'questions': st.column_config.NumberColumn('Fragen'),
            'runtime_avg': st.column_config.NumberColumn('Ø Zeit (ms)', format="%.1f"),
            'token_avg': st.column_config.NumberColumn('Ø Tokens'),
            'quality_avg': st.column_config.NumberColumn('Ø Qualität', format="%.3f"),
            'performance': st.column_config.NumberColumn('Performance (T/s)', format="%.2f")
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
    st.header("📝 Log-Analyse")
    
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
        level_filter = st.selectbox(
            "Log-Level:",
            ["Alle"] + list(log_df['level'].unique())
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
    
    # Fehler anzeigen wenn vorhanden
    if len(errors) > 0:
        st.markdown("### ❌ Fehler")
        for _, error in errors.iterrows():
            st.markdown(f"""
            <div class="error-box">
                <strong>{error['timestamp']}</strong> - {error['module']}<br>
                {error['message']}
            </div>
            """, unsafe_allow_html=True)
    
    # Warnungen anzeigen wenn vorhanden
    if len(warnings) > 0:
        st.markdown("### ⚠️ Warnungen")
        for _, warning in warnings.iterrows():
            st.markdown(f"""
            <div class="warning-box">
                <strong>{warning['timestamp']}</strong> - {warning['module']}<br>
                {warning['message']}
            </div>
            """, unsafe_allow_html=True)
    
    # Log-Tabelle
    st.markdown("### 📋 Log-Einträge")
    st.dataframe(
        filtered_df[['timestamp', 'module', 'level', 'message']],
        use_container_width=True,
        hide_index=True
    )


def show_performance(df: pd.DataFrame, results: List[Dict]):
    """Zeigt Performance-Analyse"""
    st.header("⚡ Performance-Analyse")
    
    # LLM Ladezeit-Analyse
    st.subheader("🚀 LLM Ladezeit-Analyse")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_load_time = df['llm_load_time'].mean()
        st.metric("Ø Ladezeit", f"{avg_load_time:.1f} ms" if avg_load_time > 0 else "N/A")
    
    with col2:
        max_load_time = df['llm_load_time'].max()
        st.metric("Max Ladezeit", f"{max_load_time:.1f} ms" if max_load_time > 0 else "N/A")
    
    with col3:
        avg_cold_start = df['cold_start_factor'].mean()
        st.metric("Ø Cold Start Faktor", f"{avg_cold_start:.2f}x" if avg_cold_start > 0 else "N/A")
    
    with col4:
        models_with_load_time = df[df['llm_load_time'] > 0]['model'].nunique()
        st.metric("Modelle mit Ladezeit", models_with_load_time)
    
    # Ladezeit-Vergleich
    if df['llm_load_time'].sum() > 0:
        load_time_df = df[df['llm_load_time'] > 0].copy()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Ladezeit nach Modell
            fig_load_time = px.bar(
                load_time_df,
                x='model',
                y='llm_load_time',
                color='server',
                title='LLM Ladezeit nach Modell',
                labels={'llm_load_time': 'Ladezeit (ms)', 'model': 'Modell'}
            )
            st.plotly_chart(fig_load_time, use_container_width=True)
        
        with col2:
            # Cold Start Faktor
            fig_cold_start = px.bar(
                load_time_df,
                x='model',
                y='cold_start_factor',
                color='server',
                title='Cold Start Faktor (Ladezeit/Avg Runtime)',
                labels={'cold_start_factor': 'Faktor', 'model': 'Modell'}
            )
            st.plotly_chart(fig_cold_start, use_container_width=True)
    
    st.markdown("---")
    
    # Performance-Metriken
    st.subheader("📊 Performance-Metriken (Tokens/Sekunde)")
    
    # Scatter Plot: Runtime vs Tokens
    fig_scatter = px.scatter(
        df,
        x='runtime_avg',
        y='token_avg',
        color='model',
        size='questions',
        hover_data=['server', 'quality_avg', 'llm_load_time'],
        title='Runtime vs. Tokens',
        labels={'runtime_avg': 'Durchschnittliche Laufzeit (ms)', 'token_avg': 'Durchschnittliche Tokens'}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Performance Ranking
    st.subheader("🏆 Performance-Ranking")
    
    perf_df = df[['model', 'server', 'performance', 'runtime_avg', 'token_avg', 'quality_avg']].copy()
    perf_df = perf_df.sort_values('performance', ascending=False)
    
    # Bar Chart
    fig_bar = px.bar(
        perf_df,
        x='model',
        y='performance',
        color='server',
        title='Performance nach Modell und Server',
        labels={'performance': 'Tokens/Sekunde', 'model': 'Modell'}
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Detaillierte Performance-Tabelle
    st.subheader("📋 Performance-Details")
    st.dataframe(
        perf_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'model': st.column_config.TextColumn('Modell'),
            'server': st.column_config.TextColumn('Server'),
            'performance': st.column_config.NumberColumn('Performance (T/s)', format="%.2f"),
            'runtime_avg': st.column_config.NumberColumn('Ø Zeit (ms)', format="%.1f"),
            'token_avg': st.column_config.NumberColumn('Ø Tokens'),
            'quality_avg': st.column_config.NumberColumn('Ø Qualität', format="%.3f")
        }
    )
    
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
            fig_box = px.box(
                time_df,
                x='model',
                y='time',
                title='Zeitverteilung nach Modell',
                labels={'time': 'Zeit (ms)', 'model': 'Modell'}
            )
            st.plotly_chart(fig_box, use_container_width=True)


def show_comparisons(df: pd.DataFrame, results: List[Dict]):
    """Zeigt Vergleichsanalysen"""
    st.header("🔄 Modell- und Server-Vergleiche")
    
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
            
            # Detailtabelle
            st.subheader(f"📋 Details für {selected_model}")
            st.dataframe(
                model_df[['server', 'runtime_avg', 'token_avg', 'quality_avg', 'performance']],
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
            
            # Multi-Metrik Balkendiagramm
            metrics = ['runtime_avg', 'token_avg', 'quality_avg', 'performance']
            
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Durchschnittliche Laufzeit (ms)', 'Durchschnittliche Tokens',
                               'Durchschnittliche Qualität', 'Performance (T/s)')
            )
            
            # Runtime
            fig.add_trace(
                go.Bar(x=server_df['model'], y=server_df['runtime_avg'], name='Runtime'),
                row=1, col=1
            )
            
            # Tokens
            fig.add_trace(
                go.Bar(x=server_df['model'], y=server_df['token_avg'], name='Tokens'),
                row=1, col=2
            )
            
            # Quality
            fig.add_trace(
                go.Bar(x=server_df['model'], y=server_df['quality_avg'], name='Quality'),
                row=2, col=1
            )
            
            # Performance
            fig.add_trace(
                go.Bar(x=server_df['model'], y=server_df['performance'], name='Performance'),
                row=2, col=2
            )
            
            fig.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Ranking-Tabelle
            st.subheader("🏆 Modell-Ranking")
            ranking_df = server_df[['model', 'runtime_avg', 'token_avg', 'quality_avg', 'performance']].copy()
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
        
        # Radar Chart
        st.subheader("🎯 Qualitäts-Radar")
        
        fig = go.Figure()
        
        for model in selected_models:
            if model in avg_metrics.index:
                values = avg_metrics.loc[model].values.tolist()
                values.append(values[0])  # Schließe den Kreis
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=metrics + [metrics[0]],
                    fill='toself',
                    name=model
                ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Qualitätsmetriken-Vergleich"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
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
        
        # Box Plots für einzelne Metriken
        st.subheader("📈 Metrik-Verteilungen")
        
        selected_metric = st.selectbox(
            "Metrik für Detailansicht:",
            metrics,
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        fig_box = px.box(
            filtered_quality,
            x='model',
            y=selected_metric,
            title=f'{selected_metric.replace("_", " ").title()} Verteilung',
            labels={'model': 'Modell', selected_metric: 'Score'}
        )
        st.plotly_chart(fig_box, use_container_width=True)
        
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


if __name__ == "__main__":
    main()