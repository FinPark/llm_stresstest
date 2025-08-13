#!/usr/bin/env python3
"""
Model Registry Updater für LLM Stress Test Tool
Scannt alle result/*.json Dateien und pflegt eine zentrale models.json
mit detaillierten Modellinformationen aus verschiedenen Quellen.
"""

import json
import os
import glob
import requests
import re
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import time
from pathlib import Path

class ModelRegistryUpdater:
    def __init__(self, results_dir: str = "results", config_dir: str = "config"):
        self.results_dir = results_dir
        self.config_dir = config_dir
        self.models_file = os.path.join(config_dir, "models.json")
        self.models_data = self.load_models_json()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LLM-Stresstest-ModelRegistry/1.0'
        })
        
    def load_models_json(self) -> Dict[str, Any]:
        """Lädt die existierende models.json oder erstellt neue Struktur"""
        if os.path.exists(self.models_file):
            try:
                with open(self.models_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[OK] Geladen: {self.models_file} mit {len(data.get('models', {}))} Modellen")
                    return data
            except Exception as e:
                print(f"[WARN] Fehler beim Laden von {self.models_file}: {e}")
        
        # Neue Struktur erstellen
        return {
            "last_updated": datetime.now().isoformat(),
            "models": {},
            "statistics": {
                "total_models": 0,
                "models_with_full_info": 0,
                "models_with_partial_info": 0,
                "models_without_info": 0
            }
        }
    
    def scan_result_files(self) -> Set[str]:
        """Scannt alle result/*.json Dateien und extrahiert eindeutige Modellnamen"""
        models = set()
        pattern = os.path.join(self.results_dir, "*.json")
        result_files = glob.glob(pattern)
        
        print(f"\n[SCAN] Scanne {len(result_files)} Result-Dateien...")
        
        for file_path in result_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'meta' in data and 'model' in data['meta']:
                        model_name = data['meta']['model']
                        models.add(model_name)
                        print(f"   [FILE] {os.path.basename(file_path)}: {model_name}")
            except Exception as e:
                print(f"   [WARN] Fehler beim Lesen von {file_path}: {e}")
        
        print(f"\n[INFO] Gefundene eindeutige Modelle: {len(models)}")
        return models
    
    def get_missing_models(self, found_models: Set[str]) -> List[str]:
        """Identifiziert Modelle, die noch nicht in models.json sind"""
        existing_models = set(self.models_data.get('models', {}).keys())
        missing = list(found_models - existing_models)
        
        if missing:
            print(f"\n[NEW] Neue Modelle gefunden: {len(missing)}")
            for model in missing:
                print(f"   - {model}")
        else:
            print(f"\n[OK] Alle Modelle bereits in Registry vorhanden")
        
        return missing
    
    def fetch_ollama_info(self, model_name: str) -> Optional[Dict]:
        """Holt Modellinformationen von lokaler Ollama Installation"""
        try:
            # Versuche lokale Ollama API
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                for model in models:
                    if model.get('name') == model_name:
                        return {
                            'parameter_size': model.get('details', {}).get('parameter_size'),
                            'quantization_level': model.get('details', {}).get('quantization_level'),
                            'family': model.get('details', {}).get('family'),
                            'format': model.get('details', {}).get('format'),
                            'size_bytes': model.get('size'),
                            'modified_at': model.get('modified_at'),
                            'source': 'ollama_local'
                        }
        except:
            pass
        return None
    
    def fetch_huggingface_info(self, model_name: str) -> Optional[Dict]:
        """Holt Modellinformationen von Hugging Face"""
        try:
            # Bereinige Modellname für HF-Suche
            search_name = model_name.replace(':', '-').replace('_', '-')
            
            # Versuche direkte Model-API
            api_url = f"https://huggingface.co/api/models/{search_name}"
            response = self.session.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self.parse_huggingface_data(data)
            
            # Fallback: Suche nach ähnlichen Modellen
            search_url = f"https://huggingface.co/api/models?search={search_name}&limit=5"
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                models = response.json()
                if models:
                    # Nimm das erste/beste Match
                    return self.parse_huggingface_data(models[0])
                    
        except Exception as e:
            print(f"      [WARN] HF-Fehler: {e}")
        
        return None
    
    def parse_huggingface_data(self, data: Dict) -> Dict:
        """Parst Hugging Face API Daten"""
        info = {
            'provider': self.extract_provider(data.get('id', '')),
            'license': data.get('license', 'unknown'),
            'tags': data.get('tags', [])[:10],
            'source': 'huggingface'
        }
        
        # Parameter aus Tags oder Modellname extrahieren
        model_id = data.get('id', '')
        params = self.extract_parameters_from_text(model_id)
        if params:
            info['parameters'] = params
        
        # Weitere Infos aus config wenn verfügbar
        if 'config' in data:
            config = data['config']
            info['architecture'] = config.get('model_type', 'unknown')
            info['context_length'] = config.get('max_position_embeddings')
        
        # Features erkennen
        tags = data.get('tags', [])
        info['multimodal'] = any(t in tags for t in ['vision', 'multimodal', 'image-text'])
        info['tools_support'] = any(t in tags for t in ['function-calling', 'tools'])
        info['reasoning_optimized'] = any(word in model_id.lower() 
                                         for word in ['reasoning', 'thinking', 'r1'])
        
        return info
    
    def extract_parameters_from_text(self, text: str) -> Optional[int]:
        """Extrahiert Parameter-Anzahl aus Text"""
        text = text.lower()
        
        patterns = [
            (r'(\d+\.?\d*)\s*b(?:illion)?', 1_000_000_000),
            (r'(\d+\.?\d*)\s*m(?:illion)?', 1_000_000),
            (r'(\d+\.?\d*)\s*k', 1_000),
            (r'(\d+\.?\d*)\s*t(?:rillion)?', 1_000_000_000_000),
        ]
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, text)
            if match:
                return int(float(match.group(1)) * multiplier)
        
        return None
    
    def extract_provider(self, model_id: str) -> str:
        """Extrahiert Provider aus Model ID"""
        if '/' in model_id:
            org = model_id.split('/')[0].lower()
            provider_map = {
                'meta-llama': 'meta',
                'microsoft': 'microsoft',
                'google': 'google',
                'anthropic': 'anthropic',
                'openai': 'openai',
                'mistralai': 'mistral',
                'mistral': 'mistral',
                'alibaba': 'alibaba',
                'qwen': 'alibaba',
                'deepseek': 'deepseek',
                'nvidia': 'nvidia',
                'cohere': 'cohere'
            }
            return provider_map.get(org, org)
        return "unknown"
    
    def determine_model_type(self, model_name: str, tags: List[str] = None) -> str:
        """Bestimmt den Modelltyp"""
        model_lower = model_name.lower()
        tags_lower = [t.lower() for t in (tags or [])]
        
        if 'instruct' in model_lower or 'instruct' in tags_lower:
            return 'instruct'
        elif 'chat' in model_lower or 'chat' in tags_lower:
            return 'chat'
        elif 'code' in model_lower or 'coding' in tags_lower:
            return 'code'
        elif 'base' in model_lower or 'foundation' in tags_lower:
            return 'base'
        elif any(word in model_lower for word in ['reasoning', 'thinking', 'r1']):
            return 'reasoning'
        else:
            return 'chat'  # Default
    
    def get_size_category(self, parameters: Optional[int]) -> str:
        """Kategorisiert Modellgröße"""
        if not parameters:
            return "unknown"
        
        if parameters < 1_000_000_000:
            return "tiny"      # <1B
        elif parameters < 3_000_000_000:
            return "small"     # 1-3B
        elif parameters < 10_000_000_000:
            return "medium"    # 3-10B
        elif parameters < 30_000_000_000:
            return "large"     # 10-30B
        elif parameters < 100_000_000_000:
            return "xlarge"    # 30-100B
        else:
            return "xxlarge"   # >100B
    
    def collect_model_info(self, model_name: str) -> Dict:
        """Sammelt alle verfügbaren Informationen für ein Modell"""
        print(f"\n📥 Sammle Informationen für: {model_name}")
        
        info = {
            'name': model_name,
            'added_date': datetime.now().isoformat(),
            'model_type': self.determine_model_type(model_name),
            'sources': []
        }
        
        # 1. Ollama lokale Infos
        ollama_info = self.fetch_ollama_info(model_name)
        if ollama_info:
            info.update(ollama_info)
            info['sources'].append('ollama_local')
            print(f"   [OK] Ollama-Infos gefunden")
        
        # 2. Hugging Face Infos
        time.sleep(0.5)  # Rate limiting
        hf_info = self.fetch_huggingface_info(model_name)
        if hf_info:
            # Merge mit bestehenden Infos
            for key, value in hf_info.items():
                if key not in info or info[key] in [None, 'unknown']:
                    info[key] = value
            if 'huggingface' not in info['sources']:
                info['sources'].append('huggingface')
            print(f"   [OK] Hugging Face-Infos gefunden")
        
        # 3. Aus Modellname extrahieren (Fallback)
        if 'parameters' not in info:
            params = self.extract_parameters_from_text(model_name)
            if params:
                info['parameters'] = params
                info['parameter_estimate'] = True
                print(f"   [INFO] Parameter aus Name geschätzt: {params:,}")
        
        # 4. Provider bestimmen
        if 'provider' not in info:
            info['provider'] = self.extract_provider(model_name)
        
        # 5. Größenkategorie
        if 'parameters' in info:
            info['size_category'] = self.get_size_category(info.get('parameters'))
        
        # 6. Info-Vollständigkeit bewerten
        required_fields = ['parameters', 'provider', 'model_type']
        optional_fields = ['context_length', 'architecture', 'license']
        
        has_required = sum(1 for f in required_fields if f in info and info[f] not in [None, 'unknown'])
        has_optional = sum(1 for f in optional_fields if f in info and info[f] not in [None, 'unknown'])
        
        if has_required == len(required_fields):
            if has_optional >= 2:
                info['info_quality'] = 'complete'
            else:
                info['info_quality'] = 'good'
        elif has_required >= 2:
            info['info_quality'] = 'partial'
        else:
            info['info_quality'] = 'minimal'
        
        print(f"   [INFO] Info-Qualität: {info['info_quality']}")
        
        return info
    
    def update_statistics(self):
        """Aktualisiert die Statistiken in models.json"""
        models = self.models_data.get('models', {})
        
        stats = {
            'total_models': len(models),
            'models_with_full_info': 0,
            'models_with_partial_info': 0,
            'models_without_info': 0,
            'by_provider': {},
            'by_size_category': {},
            'by_model_type': {}
        }
        
        for model_name, model_info in models.items():
            # Info-Qualität
            quality = model_info.get('info_quality', 'minimal')
            if quality in ['complete', 'good']:
                stats['models_with_full_info'] += 1
            elif quality == 'partial':
                stats['models_with_partial_info'] += 1
            else:
                stats['models_without_info'] += 1
            
            # Provider
            provider = model_info.get('provider', 'unknown')
            stats['by_provider'][provider] = stats['by_provider'].get(provider, 0) + 1
            
            # Größenkategorie
            size_cat = model_info.get('size_category', 'unknown')
            stats['by_size_category'][size_cat] = stats['by_size_category'].get(size_cat, 0) + 1
            
            # Modelltyp
            model_type = model_info.get('model_type', 'unknown')
            stats['by_model_type'][model_type] = stats['by_model_type'].get(model_type, 0) + 1
        
        self.models_data['statistics'] = stats
    
    def save_models_json(self):
        """Speichert die aktualisierte models.json"""
        self.models_data['last_updated'] = datetime.now().isoformat()
        
        try:
            with open(self.models_file, 'w', encoding='utf-8') as f:
                json.dump(self.models_data, f, indent=2, ensure_ascii=False)
            print(f"\n[OK] Gespeichert: {self.models_file}")
            print(f"   [INFO] {self.models_data['statistics']['total_models']} Modelle insgesamt")
            print(f"   [OK] {self.models_data['statistics']['models_with_full_info']} mit vollständigen Infos")
            print(f"   [WARN] {self.models_data['statistics']['models_with_partial_info']} mit teilweisen Infos")
            print(f"   [ERROR] {self.models_data['statistics']['models_without_info']} ohne Infos")
        except Exception as e:
            print(f"\n[ERROR] Fehler beim Speichern: {e}")
    
    def run(self):
        """Hauptprozess: Scannt Results und aktualisiert Model Registry"""
        print("=" * 60)
        print("[START] LLM Model Registry Updater")
        print("=" * 60)
        
        # 1. Scan result files
        found_models = self.scan_result_files()
        
        if not found_models:
            print("\n[ERROR] Keine Modelle in Result-Dateien gefunden")
            return
        
        # 2. Find missing models
        missing_models = self.get_missing_models(found_models)
        
        # 3. Fetch info for missing models
        if missing_models:
            print(f"\n[FETCH] Hole Informationen für {len(missing_models)} neue Modelle...")
            
            for model_name in missing_models:
                try:
                    model_info = self.collect_model_info(model_name)
                    self.models_data['models'][model_name] = model_info
                except Exception as e:
                    print(f"\n[ERROR] Fehler bei {model_name}: {e}")
                    # Minimale Info speichern
                    self.models_data['models'][model_name] = {
                        'name': model_name,
                        'added_date': datetime.now().isoformat(),
                        'info_quality': 'minimal',
                        'error': str(e)
                    }
        
        # 4. Update statistics
        self.update_statistics()
        
        # 5. Save updated registry
        self.save_models_json()
        
        # 6. Summary
        print("\n" + "=" * 60)
        print("[SUMMARY] ZUSAMMENFASSUNG")
        print("=" * 60)
        
        if missing_models:
            print(f"[OK] {len(missing_models)} neue Modelle zur Registry hinzugefügt")
        else:
            print("[INFO] Keine neuen Modelle hinzugefügt")
        
        # Provider-Übersicht
        if self.models_data['statistics'].get('by_provider'):
            print(f"\n[PACKAGE] Modelle nach Provider:")
            for provider, count in sorted(self.models_data['statistics']['by_provider'].items()):
                print(f"   {provider}: {count}")
        
        # Größen-Übersicht
        if self.models_data['statistics'].get('by_size_category'):
            print(f"\n[SIZE] Modelle nach Größe:")
            size_order = ['tiny', 'small', 'medium', 'large', 'xlarge', 'xxlarge', 'unknown']
            for size in size_order:
                if size in self.models_data['statistics']['by_size_category']:
                    count = self.models_data['statistics']['by_size_category'][size]
                    print(f"   {size}: {count}")


def main():
    """Hauptfunktion"""
    updater = ModelRegistryUpdater()
    updater.run()


if __name__ == "__main__":
    main()