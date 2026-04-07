# CS2 DataLab - Project Context & Guidelines

## Overview
This project is a CS2 (Counter-Strike 2) data analysis pipeline designed to extract, parse, analyze, and visualize match data (demo files). It utilizes a microservices architecture with Docker Compose, involving various components for data processing and visualization.

## Architecture
- **Parser (`/parser`):** Handles the extraction of raw data from CS2 demo files.
- **Analyzer (`/analyzer`):** Processes parsed data to generate tactical insights and metrics.
- **Generator (`/generator`):** Responsible for creating visual assets and reports.
- **n8n (`/n8n`):** Orchestrates the data pipeline workflows.
- **Postgres:** Database for storing match data and analysis results.
- **Nginx:** Web server for serving visualizations and potentially an API.
- **Scripts (`/scripts`):** Utility scripts for manual execution, visualization, and pipeline management.

## Interaction Guidelines
- **Python Code:** Follow PEP 8. Use type hints where possible.
- **Shell Scripts:** Use `bash`. Ensure scripts are executable and include error handling.
- **Docker:** When modifying `Dockerfile`s or `docker-compose.yml`, ensure configurations are optimized for development and production (e.g., volume mounts, environment variables).
- **Data Integrity:** Be cautious when modifying files in `raw/`, `parsed/`, or `data/` as these are intermediate/final data stores.
- **Visuals:** Visualizations are generated into the `visuals/` directory.

## Key Directories
- `scripts/`: Contains CLIs for visualization and pipeline steps.
- `features/`: Stores tactical summaries and AI prompts.
- `raw/` & `parsed/`: Data storage for different stages of the pipeline.
- `n8n/`: Workflow definitions.
