#!/usr/bin/env python3
"""
LLM Quality Evaluator
Objektive Qualitätsbewertung von LLM-Antworten mit verschiedenen Metriken
"""

import json
import re
import math
import statistics
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import argparse

# Optional: Für erweiterte NLP-Features
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


@dataclass
class QualityMetrics:
    """Container für alle Qualitätsmetriken"""
    # Strukturelle Metriken (0-1, höher = besser)
    structure_score: float
    readability_score: float
    completeness_score: float
    
    # Inhaltliche Metriken (0-1, höher = besser)
    relevance_score: float
    factual_consistency: float
    
    # Sprachliche Metriken (0-1, höher = besser)
    fluency_score: float
    coherence_score: float
    
    # Gesamtbewertung (0-1, höher = besser)
    overall_quality: float
    
    # Zusätzliche Informationen
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    unique_words_ratio: float


class LLMQualityEvaluator:
    """Klasse für die objektive Bewertung von LLM-Antworten"""
    
    def __init__(self):
        self.reference_answers = {}
        self.semantic_model = None
        self.nlp = None
        
        # Lade Modelle falls verfügbar
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.semantic_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                print("✓ Semantic Similarity Model geladen")
            except Exception as e:
                print(f"⚠ Semantic Model konnte nicht geladen werden: {e}")
        
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("de_core_news_sm")
                print("✓ SpaCy Deutsch Model geladen")
            except Exception:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                    print("✓ SpaCy English Model geladen")
                except Exception as e:
                    print(f"⚠ SpaCy Model konnte nicht geladen werden: {e}")
    
    def load_reference_answers(self, reference_file: str):
        """Lädt Referenzantworten für Vergleiche"""
        try:
            with open(reference_file, 'r', encoding='utf-8') as f:
                self.reference_answers = json.load(f)
            print(f"✓ {len(self.reference_answers)} Referenzantworten geladen")
        except FileNotFoundError:
            print(f"⚠ Referenzdatei {reference_file} nicht gefunden - verwende heuristische Bewertung")
        except Exception as e:
            print(f"⚠ Fehler beim Laden der Referenzen: {e}")
    
    def evaluate_structure(self, answer: str) -> float:
        """Bewertet die strukturelle Qualität der Antwort"""
        score = 0.0
        max_score = 5.0
        
        # 1. Hat die Antwort Absätze? (0.2)
        if '\n\n' in answer or '\n' in answer:
            score += 1.0
        
        # 2. Verwendet Aufzählungen oder Listen? (0.2)
        if re.search(r'[•\-\*]\s|\d+\.\s|[a-z]\)\s', answer):
            score += 1.0
        
        # 3. Hat Überschriften oder Hervorhebungen? (0.2)
        if re.search(r'\*\*.*?\*\*|__.*?__|###|##', answer):
            score += 1.0
        
        # 4. Angemessene Länge (nicht zu kurz, nicht zu lang) (0.2)
        word_count = len(answer.split())
        if 50 <= word_count <= 1000:
            score += 1.0
        elif word_count > 1000:
            score += 0.5  # Zu lang ist auch nicht ideal
        
        # 5. Hat Beispiele oder Erklärungen? (0.2)
        if re.search(r'beispiel|z\.?b\.?|etwa|wie|stell.*vor', answer.lower()):
            score += 1.0
        
        return min(score / max_score, 1.0)
    
    def evaluate_readability(self, answer: str) -> float:
        """Bewertet die Lesbarkeit (vereinfachter Flesch-Score)"""
        sentences = re.split(r'[.!?]+', answer)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        words = answer.split()
        if not words:
            return 0.0
        
        # Durchschnittliche Satzlänge
        avg_sentence_length = len(words) / len(sentences)
        
        # Durchschnittliche Wortlänge (Proxy für Silben)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Vereinfachter Readability Score (je niedriger die Werte, desto besser lesbar)
        # Ideale Werte: 15-20 Wörter pro Satz, 4-6 Zeichen pro Wort
        sentence_penalty = max(0, avg_sentence_length - 20) / 50
        word_penalty = max(0, avg_word_length - 6) / 10
        
        readability = 1.0 - (sentence_penalty + word_penalty)
        return max(0.0, min(1.0, readability))
    
    def evaluate_completeness(self, answer: str, question: str) -> float:
        """Bewertet die Vollständigkeit der Antwort"""
        score = 0.0
        max_score = 4.0
        
        answer_lower = answer.lower()
        question_lower = question.lower()
        
        # 1. Mindestlänge erreicht (0.25)
        if len(answer.split()) >= 30:
            score += 1.0
        
        # 2. Bezieht sich auf die Frage (0.25)
        # Extrahiere Schlüsselwörter aus der Frage
        question_words = set(re.findall(r'\b\w{4,}\b', question_lower))
        answer_words = set(re.findall(r'\b\w{4,}\b', answer_lower))
        
        if question_words:
            word_overlap = len(question_words.intersection(answer_words)) / len(question_words)
            score += word_overlap
        
        # 3. Hat eine Einleitung (0.25)
        intro_patterns = ['zunächst', 'erstens', 'um das zu', 'lass uns', 'stell dir vor', 'kurz gesagt']
        if any(pattern in answer_lower for pattern in intro_patterns):
            score += 1.0
        
        # 4. Hat einen Abschluss/Zusammenfassung (0.25)
        conclusion_patterns = ['zusammenfassend', 'fazit', 'abschließend', 'insgesamt', 'kurz gesagt']
        if any(pattern in answer_lower for pattern in conclusion_patterns):
            score += 1.0
        
        return min(score / max_score, 1.0)
    
    def evaluate_relevance(self, answer: str, question: str) -> float:
        """Bewertet die Relevanz der Antwort zur Frage"""
        if self.semantic_model and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Semantic Similarity mit Sentence Transformers
                question_embedding = self.semantic_model.encode([question])
                answer_embedding = self.semantic_model.encode([answer])
                
                # Cosine Similarity
                similarity = float(self.semantic_model.similarity(question_embedding, answer_embedding)[0][0])
                return max(0.0, min(1.0, similarity))
            except Exception as e:
                print(f"⚠ Semantic similarity Fehler: {e}")
        
        # Fallback: Keyword-basierte Relevanz
        return self._keyword_relevance(answer, question)
    
    def _keyword_relevance(self, answer: str, question: str) -> float:
        """Fallback-Methode für Relevanz basierend auf Schlüsselwörtern"""
        # Extrahiere wichtige Wörter (keine Stopwörter)
        stopwords = {'der', 'die', 'das', 'und', 'oder', 'aber', 'in', 'auf', 'mit', 'zu', 'ist', 'sind', 'was', 'wie', 'wo', 'wann', 'warum'}
        
        question_words = set(word.lower() for word in re.findall(r'\b\w{3,}\b', question) if word.lower() not in stopwords)
        answer_words = set(word.lower() for word in re.findall(r'\b\w{3,}\b', answer) if word.lower() not in stopwords)
        
        if not question_words:
            return 0.5
        
        # Jaccard Similarity
        intersection = len(question_words.intersection(answer_words))
        union = len(question_words.union(answer_words))
        
        return intersection / union if union > 0 else 0.0
    
    def evaluate_fluency(self, answer: str) -> float:
        """Bewertet die sprachliche Flüssigkeit"""
        score = 0.0
        max_score = 4.0
        
        # 1. Keine offensichtlichen Grammatikfehler (vereinfacht)
        # Suche nach häufigen Fehlern
        grammar_errors = 0
        grammar_errors += len(re.findall(r'\b(\w+)\s+\1\b', answer))  # Wortwiederholungen
        grammar_errors += len(re.findall(r'[a-z]\.[A-Z]', answer))  # Fehlende Leerzeichen nach Punkt
        
        if grammar_errors == 0:
            score += 1.0
        elif grammar_errors <= 2:
            score += 0.5
        
        # 2. Korrekte Interpunktion
        sentences = re.split(r'[.!?]', answer)
        if len([s for s in sentences if s.strip()]) > 1:  # Mehr als ein Satz
            score += 1.0
        
        # 3. Abwechslungsreiche Satzstrukturen
        sentence_starts = [s.strip()[:10] for s in sentences if s.strip()]
        unique_starts = len(set(sentence_starts))
        if len(sentence_starts) > 0:
            variety_ratio = unique_starts / len(sentence_starts)
            score += variety_ratio
        
        # 4. Natürlicher Sprachfluss (keine robotische Sprache)
        natural_indicators = ['übrigens', 'allerdings', 'jedoch', 'außerdem', 'zudem', 'deshalb', 'daher']
        if any(indicator in answer.lower() for indicator in natural_indicators):
            score += 1.0
        
        return min(score / max_score, 1.0)
    
    def evaluate_coherence(self, answer: str) -> float:
        """Bewertet die logische Kohärenz"""
        score = 0.0
        max_score = 3.0
        
        # 1. Logische Verbindungswörter
        connectors = ['deshalb', 'daher', 'folglich', 'außerdem', 'zudem', 'jedoch', 'allerdings', 'trotzdem']
        connector_count = sum(1 for connector in connectors if connector in answer.lower())
        score += min(connector_count / 3, 1.0)
        
        # 2. Thematische Konsistenz (wiederkehrende Schlüsselwörter)
        words = re.findall(r'\b\w{4,}\b', answer.lower())
        if words:
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Bewerte wiederkehrende Begriffe (deutet auf thematische Kohärenz hin)
            recurring_words = [w for w, count in word_freq.items() if count >= 2]
            if len(words) > 0:
                coherence_ratio = len(recurring_words) / len(set(words))
                score += min(coherence_ratio * 2, 1.0)
        
        # 3. Strukturelle Progression (Aufbau erkennbar)
        paragraphs = answer.split('\n\n')
        if len(paragraphs) > 1:
            score += 1.0
        
        return min(score / max_score, 1.0)
    
    def evaluate_factual_consistency(self, answer: str) -> float:
        """Bewertet die faktische Konsistenz (vereinfacht)"""
        score = 1.0  # Standard: Annahme, dass keine Widersprüche vorliegen
        
        # Suche nach offensichtlichen Widersprüchen
        # Dies ist eine sehr vereinfachte Implementierung
        
        # 1. Widersprüchliche Aussagen zu Zahlen
        numbers = re.findall(r'\b\d+\b', answer)
        if len(set(numbers)) != len(numbers) and len(numbers) > 1:
            # Gleiche Zahlen könnten widersprüchlich verwendet werden
            score -= 0.1
        
        # 2. Selbstwidersprüche (vereinfacht)
        contradiction_patterns = [
            (r'immer', r'nie'),
            (r'alle', r'keine'),
            (r'möglich', r'unmöglich'),
            (r'richtig', r'falsch')
        ]
        
        for pos_pattern, neg_pattern in contradiction_patterns:
            if re.search(pos_pattern, answer.lower()) and re.search(neg_pattern, answer.lower()):
                score -= 0.2
        
        return max(0.0, score)
    
    def calculate_additional_metrics(self, answer: str) -> Dict[str, float]:
        """Berechnet zusätzliche Metriken"""
        words = answer.split()
        sentences = re.split(r'[.!?]+', answer)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        unique_words = set(word.lower() for word in words)
        
        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_sentence_length': len(words) / max(len(sentences), 1),
            'unique_words_ratio': len(unique_words) / max(len(words), 1)
        }
    
    def evaluate_answer(self, question: str, answer: str) -> QualityMetrics:
        """Hauptmethode zur Bewertung einer Antwort"""
        # Strukturelle Bewertung
        structure_score = self.evaluate_structure(answer)
        readability_score = self.evaluate_readability(answer)
        completeness_score = self.evaluate_completeness(answer, question)
        
        # Inhaltliche Bewertung
        relevance_score = self.evaluate_relevance(answer, question)
        factual_consistency = self.evaluate_factual_consistency(answer)
        
        # Sprachliche Bewertung
        fluency_score = self.evaluate_fluency(answer)
        coherence_score = self.evaluate_coherence(answer)
        
        # Gewichtete Gesamtbewertung
        weights = {
            'relevance': 0.25,      # Sehr wichtig
            'completeness': 0.20,   # Wichtig
            'fluency': 0.15,        # Wichtig
            'structure': 0.15,      # Wichtig
            'coherence': 0.10,      # Moderat wichtig
            'readability': 0.10,    # Moderat wichtig
            'factual': 0.05        # Basis-Check
        }
        
        overall_quality = (
            relevance_score * weights['relevance'] +
            completeness_score * weights['completeness'] +
            fluency_score * weights['fluency'] +
            structure_score * weights['structure'] +
            coherence_score * weights['coherence'] +
            readability_score * weights['readability'] +
            factual_consistency * weights['factual']
        )
        
        # Zusätzliche Metriken
        additional_metrics = self.calculate_additional_metrics(answer)
        
        return QualityMetrics(
            structure_score=round(structure_score, 3),
            readability_score=round(readability_score, 3),
            completeness_score=round(completeness_score, 3),
            relevance_score=round(relevance_score, 3),
            factual_consistency=round(factual_consistency, 3),
            fluency_score=round(fluency_score, 3),
            coherence_score=round(coherence_score, 3),
            overall_quality=round(overall_quality, 3),
            word_count=additional_metrics['word_count'],
            sentence_count=additional_metrics['sentence_count'],
            avg_sentence_length=round(additional_metrics['avg_sentence_length'], 1),
            unique_words_ratio=round(additional_metrics['unique_words_ratio'], 3)
        )
    
    def evaluate_dataset(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bewertet einen ganzen Datensatz"""
        results = []
        
        print(f"Bewerte {len(data)} Antworten...")
        
        for i, item in enumerate(data):
            question = item.get('question', '')
            answer = item.get('answer', '')
            
            if not question or not answer:
                print(f"⚠ Überspringe Item {i}: Frage oder Antwort fehlt")
                continue
            
            metrics = self.evaluate_answer(question, answer)
            
            # Erstelle neues Item mit allen ursprünglichen Daten plus Bewertung
            result_item = item.copy()
            result_item['quality_metrics'] = {
                'structure_score': metrics.structure_score,
                'readability_score': metrics.readability_score,
                'completeness_score': metrics.completeness_score,
                'relevance_score': metrics.relevance_score,
                'factual_consistency': metrics.factual_consistency,
                'fluency_score': metrics.fluency_score,
                'coherence_score': metrics.coherence_score,
                'overall_quality': metrics.overall_quality,
                'word_count': metrics.word_count,
                'sentence_count': metrics.sentence_count,
                'avg_sentence_length': metrics.avg_sentence_length,
                'unique_words_ratio': metrics.unique_words_ratio
            }
            
            # Überschreibe das alte quality Feld
            result_item['quality'] = metrics.overall_quality
            
            results.append(result_item)
            
            if (i + 1) % 10 == 0:
                print(f"  {i + 1}/{len(data)} abgeschlossen")
        
        return results
    
    def generate_quality_report(self, evaluated_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generiert einen Bericht über die Qualitätsmetriken"""
        if not evaluated_data:
            return {"error": "Keine Daten zum Auswerten"}
        
        # Sammle alle Metriken
        all_metrics = {}
        metric_names = ['overall_quality', 'structure_score', 'readability_score', 
                       'completeness_score', 'relevance_score', 'factual_consistency',
                       'fluency_score', 'coherence_score']
        
        for metric in metric_names:
            values = [item['quality_metrics'][metric] for item in evaluated_data if 'quality_metrics' in item]
            if values:
                all_metrics[metric] = {
                    'mean': round(statistics.mean(values), 3),
                    'median': round(statistics.median(values), 3),
                    'min': round(min(values), 3),
                    'max': round(max(values), 3),
                    'stddev': round(statistics.stdev(values) if len(values) > 1 else 0, 3)
                }
        
        # Performance-Qualitäts-Korrelation
        quality_scores = [item['quality'] for item in evaluated_data]
        time_scores = [item.get('time', 0) for item in evaluated_data]
        token_scores = [item.get('token', 0) for item in evaluated_data]
        
        report = {
            'summary': {
                'total_evaluated': len(evaluated_data),
                'avg_quality': round(statistics.mean(quality_scores), 3),
                'quality_distribution': {
                    'excellent': len([q for q in quality_scores if q >= 0.8]),
                    'good': len([q for q in quality_scores if 0.6 <= q < 0.8]),
                    'acceptable': len([q for q in quality_scores if 0.4 <= q < 0.6]),
                    'poor': len([q for q in quality_scores if q < 0.4])
                }
            },
            'metrics_statistics': all_metrics,
            'performance_quality_analysis': {
                'avg_time_per_quality_point': round(sum(time_scores) / sum(quality_scores) if sum(quality_scores) > 0 else 0, 1),
                'avg_tokens_per_quality_point': round(sum(token_scores) / sum(quality_scores) if sum(quality_scores) > 0 else 0, 1),
                'quality_efficiency': round(sum(quality_scores) / (sum(time_scores) / 1000) if sum(time_scores) > 0 else 0, 3)
            }
        }
        
        return report


def main():
    parser = argparse.ArgumentParser(description='LLM Quality Evaluator - Bewertet Result-JSON-Dateien vom LLM Stresstest')
    parser.add_argument('result_file', help='Result-JSON-Datei vom LLM Stresstest (results/*.json)')
    parser.add_argument('--output', '-o', help='Ausgabedatei für bewertete Result-JSON (Standard: <input>_quality.json)')
    parser.add_argument('--report', '-r', help='Ausgabedatei für Qualitätsbericht (Standard: <input>_quality_report.json)')
    parser.add_argument('--references', help='JSON-Datei mit Referenzantworten')
    
    args = parser.parse_args()
    
    # Lade Result-JSON-Datei
    try:
        with open(args.result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
    except Exception as e:
        print(f"Fehler beim Laden der Result-Datei: {e}")
        return
    
    # Validiere Result-JSON-Format
    if not isinstance(result_data, dict) or 'results' not in result_data:
        print(f"❌ Ungültiges Result-JSON-Format. Erwartet: {{'meta': {...}, 'results': [...], 'aggregate': {...}}}")
        return
        
    if not isinstance(result_data['results'], list):
        print(f"❌ 'results' muss eine Liste sein")
        return
        
    print(f"✓ Result-JSON geladen: {len(result_data['results'])} Antworten gefunden")
    
    # Initialisiere Evaluator
    evaluator = LLMQualityEvaluator()
    
    # Lade Referenzen falls vorhanden
    if args.references:
        evaluator.load_reference_answers(args.references)
    
    # Bewerte die Results
    evaluated_results = evaluator.evaluate_dataset(result_data['results'])
    
    # Erstelle neue Result-JSON mit Qualitätsbewertungen
    enhanced_result = result_data.copy()
    enhanced_result['results'] = evaluated_results
    
    # Berechne neue Aggregats mit Quality-Metriken
    if evaluated_results:
        quality_scores = [r['quality'] for r in evaluated_results]
        enhanced_result['aggregate']['quality_sum'] = round(sum(quality_scores), 3)
        enhanced_result['aggregate']['quality_avg'] = round(sum(quality_scores) / len(quality_scores), 3)
        enhanced_result['aggregate']['quality_min'] = round(min(quality_scores), 3)
        enhanced_result['aggregate']['quality_max'] = round(max(quality_scores), 3)
    
    # Standard-Ausgabedateinamen generieren
    input_path = Path(args.result_file)
    base_name = input_path.stem
    
    output_file = args.output or f"{input_path.parent / base_name}_quality.json"
    report_file = args.report or f"{input_path.parent / base_name}_quality_report.json"
    
    # Speichere erweiterte Result-JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enhanced_result, f, indent=2, ensure_ascii=False)
    print(f"✓ Erweiterte Result-JSON gespeichert: {output_file}")
    
    # Generiere und speichere Qualitätsbericht
    report = evaluator.generate_quality_report(evaluated_results)
    
    # Erweitere Bericht um Meta-Daten aus Original-Result
    report['original_meta'] = result_data.get('meta', {})
    report['evaluation_timestamp'] = Path(args.result_file).stat().st_mtime
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"✓ Qualitätsbericht gespeichert: {report_file}")
    
    # Zeige erweiterte Zusammenfassung
    print("\n" + "="*70)
    print("QUALITÄTSBEWERTUNG ZUSAMMENFASSUNG")
    print("="*70)
    print(f"Original Result-Datei: {args.result_file}")
    print(f"LLM-Server: {result_data.get('meta', {}).get('server', 'Unbekannt')}")
    print(f"Modell: {result_data.get('meta', {}).get('model', 'Unbekannt')}")
    print(f"Bewertete Antworten: {report['summary']['total_evaluated']}")
    print(f"Durchschnittliche Qualität: {report['summary']['avg_quality']}")
    print(f"Performance vs. Qualität: {report['performance_quality_analysis']['quality_efficiency']:.3f} Qualität/Sekunde")
    print("-" * 40)
    print(f"Exzellent (≥0.8): {report['summary']['quality_distribution']['excellent']}")
    print(f"Gut (0.6-0.8): {report['summary']['quality_distribution']['good']}")
    print(f"Akzeptabel (0.4-0.6): {report['summary']['quality_distribution']['acceptable']}")
    print(f"Schlecht (<0.4): {report['summary']['quality_distribution']['poor']}")
    
    # Empfehlungen basierend auf Qualitätsbewertung
    avg_quality = report['summary']['avg_quality']
    print("\n" + "-" * 40)
    if avg_quality >= 0.8:
        print("🎉 Exzellente Modell-Performance!")
    elif avg_quality >= 0.6:
        print("✓ Gute Modell-Performance")  
    elif avg_quality >= 0.4:
        print("⚠ Akzeptable Performance - Verbesserungen möglich")
    else:
        print("❌ Schwache Performance - Modell oder Konfiguration überprüfen")


if __name__ == "__main__":
    main()