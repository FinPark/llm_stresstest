#!/usr/bin/env python3
"""
LLM Stress Test Tool
Tests LLM performance and hardware requirements with configurable parameters.
"""

import json
import sys
import asyncio
import aiohttp
import logging
import time
import re
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from openai import AsyncOpenAI
import traceback
from dataclasses import dataclass

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


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'llm_stresstest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Container für alle Qualitätsmetriken"""
    structure_score: float
    readability_score: float
    completeness_score: float
    relevance_score: float
    factual_consistency: float
    fluency_score: float
    coherence_score: float
    overall_quality: float
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    unique_words_ratio: float


class QualityEvaluator:
    """Klasse für die objektive Bewertung von LLM-Antworten"""
    
    def __init__(self):
        self.semantic_model = None
        
        # Lade Semantic Model falls verfügbar (optional)
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.semantic_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                logger.info("✓ Semantic Similarity Model geladen")
            except Exception as e:
                logger.warning(f"Semantic Model konnte nicht geladen werden: {e}")
    
    def evaluate_structure(self, answer: str) -> float:
        """Bewertet die strukturelle Qualität der Antwort"""
        score = 0.0
        max_score = 5.0
        
        # 1. Hat die Antwort Absätze?
        if '\n\n' in answer or '\n' in answer:
            score += 1.0
        
        # 2. Verwendet Aufzählungen oder Listen?
        if re.search(r'[•\-\*]\s|\d+\.\s|[a-z]\)\s', answer):
            score += 1.0
        
        # 3. Hat Überschriften oder Hervorhebungen?
        if re.search(r'\*\*.*?\*\*|__.*?__|###|##', answer):
            score += 1.0
        
        # 4. Angemessene Länge
        word_count = len(answer.split())
        if 50 <= word_count <= 1000:
            score += 1.0
        elif word_count > 1000:
            score += 0.5
        
        # 5. Hat Beispiele oder Erklärungen?
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
        # Durchschnittliche Wortlänge
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Vereinfachter Readability Score
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
        
        # 1. Mindestlänge erreicht
        if len(answer.split()) >= 30:
            score += 1.0
        
        # 2. Bezieht sich auf die Frage
        question_words = set(re.findall(r'\b\w{4,}\b', question_lower))
        answer_words = set(re.findall(r'\b\w{4,}\b', answer_lower))
        
        if question_words:
            word_overlap = len(question_words.intersection(answer_words)) / len(question_words)
            score += word_overlap
        
        # 3. Hat eine Einleitung
        intro_patterns = ['zunächst', 'erstens', 'um das zu', 'lass uns', 'stell dir vor', 'kurz gesagt']
        if any(pattern in answer_lower for pattern in intro_patterns):
            score += 1.0
        
        # 4. Hat einen Abschluss/Zusammenfassung
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
                logger.debug(f"Semantic similarity Fehler: {e}")
        
        # Fallback: Keyword-basierte Relevanz
        return self._keyword_relevance(answer, question)
    
    def _keyword_relevance(self, answer: str, question: str) -> float:
        """Fallback-Methode für Relevanz basierend auf Schlüsselwörtern"""
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
        
        # 1. Keine offensichtlichen Grammatikfehler
        grammar_errors = 0
        grammar_errors += len(re.findall(r'\b(\w+)\s+\1\b', answer))  # Wortwiederholungen
        grammar_errors += len(re.findall(r'[a-z]\.[A-Z]', answer))  # Fehlende Leerzeichen nach Punkt
        
        if grammar_errors == 0:
            score += 1.0
        elif grammar_errors <= 2:
            score += 0.5
        
        # 2. Korrekte Interpunktion
        sentences = re.split(r'[.!?]', answer)
        if len([s for s in sentences if s.strip()]) > 1:
            score += 1.0
        
        # 3. Abwechslungsreiche Satzstrukturen
        sentence_starts = [s.strip()[:10] for s in sentences if s.strip()]
        unique_starts = len(set(sentence_starts))
        if len(sentence_starts) > 0:
            variety_ratio = unique_starts / len(sentence_starts)
            score += variety_ratio
        
        # 4. Natürlicher Sprachfluss
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
            
            recurring_words = [w for w, count in word_freq.items() if count >= 2]
            if len(words) > 0:
                coherence_ratio = len(recurring_words) / len(set(words))
                score += min(coherence_ratio * 2, 1.0)
        
        # 3. Strukturelle Progression
        paragraphs = answer.split('\n\n')
        if len(paragraphs) > 1:
            score += 1.0
        
        return min(score / max_score, 1.0)
    
    def evaluate_factual_consistency(self, answer: str) -> float:
        """Bewertet die faktische Konsistenz (vereinfacht)"""
        score = 1.0
        
        # Suche nach Widersprüchen
        numbers = re.findall(r'\b\d+\b', answer)
        if len(set(numbers)) != len(numbers) and len(numbers) > 1:
            score -= 0.1
        
        # Selbstwidersprüche
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
            'relevance': 0.25,
            'completeness': 0.20,
            'fluency': 0.15,
            'structure': 0.15,
            'coherence': 0.10,
            'readability': 0.10,
            'factual': 0.05
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


class LLMStressTest:
    def __init__(self, output_filename: str):
        self.output_filename = output_filename
        self.config = {}
        self.questions = []
        self.results = []
        self.start_time = None
        self.end_time = None
        self.client = None
        self.quality_evaluator = QualityEvaluator()
        
    def load_config(self) -> bool:
        """Load and validate configuration from config.json"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            required_fields = ['questions', 'concurrent', 'url', 'model', 'timeout']
            for field in required_fields:
                if field not in self.config:
                    logger.error(f"Missing required field in config: {field}")
                    return False
            
            logger.info(f"Configuration loaded: {self.config}")
            return True
            
        except FileNotFoundError:
            logger.error("config.json not found")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config.json: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return False
    
    def load_questions(self) -> bool:
        """Load questions from questions.json"""
        try:
            with open('questions.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'fragen' not in data:
                logger.error("'fragen' key not found in questions.json")
                return False
            
            all_questions = data['fragen']
            num_questions = min(self.config['questions'], len(all_questions))
            self.questions = all_questions[:num_questions]
            
            logger.info(f"Loaded {len(self.questions)} questions")
            return True
            
        except FileNotFoundError:
            logger.error("questions.json not found")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in questions.json: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading questions: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test connection to LLM server"""
        try:
            base_url = self.config['url']
            if not base_url.endswith('/'):
                base_url += '/'
            base_url += 'v1'
            
            self.client = AsyncOpenAI(
                base_url=base_url,
                api_key="dummy-key",
                timeout=self.config['timeout']
            )
            
            logger.info(f"Testing connection to {base_url}")
            
            response = await self.client.models.list()
            logger.info(f"Connection successful. Available models: {[m.id for m in response.data]}")
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def send_question(self, question: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Send a single question to the LLM and measure response"""
        result = {
            "question": question,
            "answer": "",
            "time": 0.0,
            "token": 0,
            "quality": 0.0
        }
        
        start_time = time.time()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config['model'],
                messages=[
                    {"role": "user", "content": question}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            end_time = time.time()
            elapsed_ms = (end_time - start_time) * 1000
            
            result["answer"] = response.choices[0].message.content
            result["time"] = round(elapsed_ms, 1)
            result["token"] = response.usage.completion_tokens if response.usage else 0
            
            # Berechne Qualitätsmetriken
            if result["answer"] and not result["answer"].startswith("ERROR"):
                try:
                    quality_metrics = self.quality_evaluator.evaluate_answer(question, result["answer"])
                    result["quality"] = quality_metrics.overall_quality
                    result["quality_metrics"] = {
                        "structure_score": quality_metrics.structure_score,
                        "readability_score": quality_metrics.readability_score,
                        "completeness_score": quality_metrics.completeness_score,
                        "relevance_score": quality_metrics.relevance_score,
                        "factual_consistency": quality_metrics.factual_consistency,
                        "fluency_score": quality_metrics.fluency_score,
                        "coherence_score": quality_metrics.coherence_score,
                        "overall_quality": quality_metrics.overall_quality,
                        "word_count": quality_metrics.word_count,
                        "sentence_count": quality_metrics.sentence_count,
                        "avg_sentence_length": quality_metrics.avg_sentence_length,
                        "unique_words_ratio": quality_metrics.unique_words_ratio
                    }
                    logger.info(f"Question processed in {elapsed_ms:.1f}ms, {result['token']} tokens, quality: {quality_metrics.overall_quality}")
                except Exception as e:
                    logger.warning(f"Quality evaluation failed: {e}")
                    result["quality"] = 0.0
                    result["quality_metrics"] = None
            else:
                logger.info(f"Question processed in {elapsed_ms:.1f}ms, {result['token']} tokens")
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout for question: {question[:50]}...")
            result["answer"] = "TIMEOUT_ERROR"
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            logger.debug(traceback.format_exc())
            result["answer"] = f"ERROR: {str(e)}"
        
        return result
    
    async def process_questions_batch(self, questions_batch: List[str], session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """Process a batch of questions concurrently"""
        tasks = [self.send_question(q, session) for q in questions_batch]
        return await asyncio.gather(*tasks)
    
    async def run_test(self) -> bool:
        """Run the complete stress test"""
        try:
            if not await self.test_connection():
                logger.error("Connection test failed. Aborting.")
                return False
            
            self.start_time = datetime.now()
            start_timestamp = time.time()
            
            connector = aiohttp.TCPConnector(
                limit=self.config.get('max_keepalive_connections', 20)
            )
            
            async with aiohttp.ClientSession(connector=connector) as session:
                concurrent = self.config['concurrent']
                
                if concurrent > 1:
                    logger.info(f"Processing questions with concurrency: {concurrent}")
                    
                    for i in range(0, len(self.questions), concurrent):
                        batch = self.questions[i:i+concurrent]
                        batch_results = await self.process_questions_batch(batch, session)
                        self.results.extend(batch_results)
                else:
                    logger.info("Processing questions sequentially")
                    
                    for question in self.questions:
                        result = await self.send_question(question, session)
                        self.results.append(result)
            
            self.end_time = datetime.now()
            end_timestamp = time.time()
            
            total_duration_ms = (end_timestamp - start_timestamp) * 1000
            
            self.save_results(total_duration_ms)
            
            logger.info(f"Test completed successfully. Results saved to results/{self.output_filename}.json")
            return True
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def calculate_aggregates(self) -> Dict[str, float]:
        """Calculate aggregate statistics from results"""
        if not self.results:
            return {}
        
        runtimes = [r['time'] for r in self.results if r['time'] > 0]
        tokens = [r['token'] for r in self.results if r['token'] > 0]
        qualities = [r['quality'] for r in self.results if r.get('quality', 0) > 0]
        
        aggregates = {
            "runtime_sum": round(sum(runtimes), 1) if runtimes else 0,
            "runtime_avg": round(sum(runtimes) / len(runtimes), 1) if runtimes else 0,
            "runtime_min": round(min(runtimes), 1) if runtimes else 0,
            "runtime_max": round(max(runtimes), 1) if runtimes else 0,
            "token_sum": sum(tokens) if tokens else 0,
            "token_avg": round(sum(tokens) / len(tokens)) if tokens else 0,
            "token_min": min(tokens) if tokens else 0,
            "token_max": max(tokens) if tokens else 0,
            "quality_sum": round(sum(qualities), 3) if qualities else 0,
            "quality_avg": round(sum(qualities) / len(qualities), 3) if qualities else 0,
            "quality_min": round(min(qualities), 3) if qualities else 0,
            "quality_max": round(max(qualities), 3) if qualities else 0
        }
        
        return aggregates
    
    def save_results(self, total_duration_ms: float):
        """Save test results to JSON file"""
        output_path = Path('results') / f"{self.output_filename}.json"
        
        output_data = {
            "meta": {
                "start_date": self.start_time.strftime("%Y-%m-%d"),
                "start_time": self.start_time.strftime("%H:%M:%S.%f")[:-3],
                "end_date": self.end_time.strftime("%Y-%m-%d"),
                "end_time": self.end_time.strftime("%H:%M:%S.%f")[:-3],
                "server": self.config['url'],
                "model": self.config['model'],
                "concurrent": self.config['concurrent'],
                "questions": self.config['questions'],
                "timeout": self.config['timeout'],
                "total_duration_ms": round(total_duration_ms, 1)
            },
            "results": self.results,
            "aggregate": self.calculate_aggregates()
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            
            with open(f"emergency_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)


async def main():
    parser = argparse.ArgumentParser(description='LLM Stress Test Tool')
    parser.add_argument('output_filename', help='Name for the output file (without .json extension)')
    
    args = parser.parse_args()
    
    if not args.output_filename:
        logger.error("Output filename is required")
        sys.exit(1)
    
    output_filename = args.output_filename.replace('.json', '')
    
    logger.info(f"Starting LLM Stress Test - Output: {output_filename}")
    
    tester = LLMStressTest(output_filename)
    
    if not tester.load_config():
        logger.error("Failed to load configuration. Exiting.")
        sys.exit(1)
    
    if not tester.load_questions():
        logger.error("Failed to load questions. Exiting.")
        sys.exit(1)
    
    success = await tester.run_test()
    
    if not success:
        logger.error("Test failed")
        sys.exit(1)
    
    logger.info("Test completed successfully")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)