# Scripts Directory - CLI Tools & Utilities

## Overview
This directory contains various Python and Shell scripts for manual execution, visualization, and match data processing.

## Script Types
- **Visualization CLIs (`vis_*_cli.py`, `visualize_awp_cli.py`):** Use these to generate specific match visuals (heatmaps, deathmaps, tactics, etc.).
- **Pipeline Scripts (`run_pipeline.sh`, `n8n_run_pipeline.sh`):** Automate the end-to-end data processing workflow.
- **Extraction & Parsing (`extract_cli.py`, `parse_demo.py`, `auto_extract_and_parse.sh`):** Tools for processing raw demo files into usable JSON data.
- **AI Prompt Generation (`generate_ai_prompt_cli.py`):** Creates prompts based on tactical summaries for LLM analysis.
- **Video Generation (`create_shorts_cli.py`, `create_long_video_cli.py`):** Tools for creating video content from match data.

## Guidelines
- **Argument Parsing:** Scripts should use `argparse` for standard CLI interfaces.
- **Error Handling:** Ensure robust error handling and logging (using the `logging` module).
- **Paths:** Be mindful of relative paths within scripts, as they are often executed from the project root or the `scripts/` directory.
- **Visuals Output:** Most visualization scripts save their output to the `../visuals/` directory.

## Map Assets
The `maps/` subdirectory contains radar images and map data used for visualizations. Refer to `visualizer.py` or `heuristics.py` for how these are utilized.
