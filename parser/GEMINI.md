# Parser Component - CS2 Demo Parsing

## Overview
The `parser` service is responsible for extracting raw data from CS2 demo files (`.dem`) and converting them into a structured JSON format for further analysis.

## Core Files
- `main.py`: The entry point for the parsing service, typically a FastAPI or simple Python script.
- `requirements.txt`: List of Python dependencies (e.g., `awpy` or similar for CS2 parsing).
- `Dockerfile`: Containerizes the parsing logic.

## Guidelines
- **Input:** Raw demo files (usually in the `raw/` directory).
- **Output:** Parsed JSON data (usually in the `parsed/` directory).
- **Tooling:** Ensure that any libraries used for parsing are compatible with the current CS2 demo format (CS2 vs CS:GO).
- **Performance:** Parsing can be resource-intensive; avoid unnecessary re-parsing if the output already exists.

## Usage
This component is typically invoked as part of the n8n pipeline or via a shell script like `scripts/auto_extract_and_parse.sh`.
