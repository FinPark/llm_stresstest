# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLM Stress Test Tool - A robust Python application for testing Large Language Models (LLMs) performance and hardware requirements. The tool sends configurable batches of questions to LLM APIs and collects detailed performance metrics.

## Development Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies
uv sync

# Run the stress test
python llm_stresstest.py <output_filename>
# Example: python llm_stresstest.py results_PC_FIN_qwen13b

# Add new dependencies
uv add <package_name>
```

## Project Structure

```
llm_stresstest/
├── config.json          # Test configuration (questions count, concurrency, timeout, etc.)
├── questions.json       # Question bank (234 questions in German)
├── llm_stresstest.py   # Main application with async processing
├── results/            # Output directory for test results
├── projectplan.md      # Detailed project planning and architecture
└── *.log              # Log files with timestamps
```

## Architecture

- **Async Processing**: Uses `asyncio` and `aiohttp` for concurrent request handling
- **OpenAI-Compatible API**: Works with any OpenAI-compatible endpoint (Ollama, vLLM, etc.)
- **Robust Error Handling**: Comprehensive try-catch blocks, no crashes on errors
- **Detailed Logging**: File and console logging with timestamps
- **Structured Output**: JSON results with metadata, individual results, and aggregates

## Configuration (config.json)

```json
{
    "questions": 5,           // Number of questions to process
    "concurrent": 1,          // Parallel requests (1 = sequential)
    "url": "http://...",     // LLM API endpoint
    "model": "model_name",   // Model identifier
    "timeout": 120.0,        // Request timeout in seconds
    "max_keepalive_connections": 20  // Connection pool size
}
```

## Output Format

Results are saved in `results/<filename>.json` with:
- **meta**: Test metadata (timestamps, server, model, duration)
- **results**: Individual question results (question, answer, time, tokens)
- **aggregate**: Statistics (sum, avg, min, max for runtime and tokens)

## Error Handling

- Connection failures abort immediately with clear error messages
- Individual question failures don't stop the test
- Emergency result saving if primary save fails
- All errors logged with stack traces in debug mode

## Testing Considerations

- Always verify connection before running tests
- Monitor log files for detailed execution info
- Check results JSON for error messages in answers
- Use concurrent > 1 for stress testing server capacity