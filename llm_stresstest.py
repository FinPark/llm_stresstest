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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from openai import AsyncOpenAI
import traceback


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'llm_stresstest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LLMStressTest:
    def __init__(self, output_filename: str):
        self.output_filename = output_filename
        self.config = {}
        self.questions = []
        self.results = []
        self.start_time = None
        self.end_time = None
        self.client = None
        
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
        
        aggregates = {
            "runtime_sum": round(sum(runtimes), 1) if runtimes else 0,
            "runtime_avg": round(sum(runtimes) / len(runtimes), 1) if runtimes else 0,
            "runtime_min": round(min(runtimes), 1) if runtimes else 0,
            "runtime_max": round(max(runtimes), 1) if runtimes else 0,
            "token_sum": sum(tokens) if tokens else 0,
            "token_avg": round(sum(tokens) / len(tokens)) if tokens else 0,
            "token_min": min(tokens) if tokens else 0,
            "token_max": max(tokens) if tokens else 0
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