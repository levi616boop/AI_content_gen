# AI_content_gen
# Automated Educational Content AI Pipeline

A modular AI system for generating high-quality educational videos from various input sources (PDFs, web content, etc.) through a multi-stage pipeline.

## Goal
To create an end-to-end automated system that transforms educational source materials into engaging video content with minimal human intervention, while maintaining high educational standards and production quality.

## Key Features
- Modular architecture for easy maintenance and upgrades
- Multi-source content ingestion (PDFs, web scraping, APIs)
- AI-powered script generation with educational best practices
- Customizable animation templates
- Multi-voice narration system
- Automated video composition
- Quality control checks at each stage
- Content management and versioning
- Self-diagnostic and repair capabilities

## Pipeline Modules
1. **Ingestion Engine**: Extracts and structures content from various sources
2. **Script Generator**: Creates educational scripts using LLMs
3. **Animator**: Generates animations based on script content
4. **Voice Generator**: Produces natural-sounding voiceovers
5. **Video Composer**: Combines all elements into final videos
6. **Uploader**: Handles publishing to various platforms
7. **Content Manager**: Tracks versions and manages assets
8. **Quality Control**: Validates output at each stage
9. **Technician Agent**: Monitors and troubleshoots the system

## Project Structure
```
.
├── src/
│   ├── ingestion_engine/
│   │   ├── __init__.py
│   │   ├── ingestion.py
│   │   └── config.py
│   ├── script_generator/
│   │   ├── __init__.py
│   │   ├── script_gen.py
│   │   ├── prompts/
│   │   │   └── educational_script_prompt.txt
│   │   └── config.py
│   ├── animator/
│   │   ├── __init__.py
│   │   ├── animate.py
│   │   ├── templates/
│   │   │   └── default_template.json
│   │   └── config.py
│   ├── voice_generator/
│   │   ├── __init__.py
│   │   ├── voice_gen.py
│   │   └── config.py
│   ├── video_composer/
│   │   ├── __init__.py
│   │   ├── compose.py
│   │   └── config.py
│   ├── uploader/
│   │   ├── __init__.py
│   │   ├── upload.py
│   │   └── config.py
│   ├── content_manager/
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   └── config.py
│   ├── quality_control/
│   │   ├── __init__.py
│   │   ├── qc_checker.py
│   │   └── config.py
│   ├── technician_agent/
│   │   ├── __init__.py
│   │   ├── technician.py
│   │   └── config.py
│   └── utils/
│       ├── __init__.py
│       ├── logging_utils.py
│       ├── file_utils.py
│       └── api_keys.py.template  (rename to api_keys.py and fill)
│
├── data/
│   ├── input/                # Raw input files (PDFs, images, URLs to scrape)
│   ├── processed/            # Intermediate processed data
│   │   ├── ingestion/        # Extracted text/JSON
│   │   ├── scripts/          # Generated scripts
│   │   ├── animations/       # Animation files (frames or mp4)
│   │   ├── voices/           # Voiceover mp3s
│   │   └── subtitles/        # Subtitle files
│   ├── output/               # Final videos
│   │   └── final_videos/
│   └── logs/
│       ├── ingestion.log
│       ├── script_generator.log
│       ├── animator.log
│       ├── voice_generator.log
│       ├── video_composer.log
│       ├── uploader.log
│       ├── content_manager.log
│       ├── quality_control.log
│       └── diagnostic.log
│
├── config/
│   ├── main_config.json      # Global configuration for the pipeline
│   └── llm_config.json       # LLM specific configurations (models, temperatures)
│
├── docs/
│   ├── architecture.md
│   └── roadmap.md
│
├── tests/
│   ├── test_ingestion.py
│   └── ... (one for each module)
│
├── .env.template             # Environment variables template (API keys, etc.)
├── .gitignore
├── requirements.txt
├── Dockerfile                # For containerization
├── README.md
├── main.py                   # Entry point for the pipeline orchestration
└── run_pipeline.sh           # Simple script to run the pipeline

## Setup Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/educational-content-ai.git
   cd educational-content-ai
2. Create and activate a virtual environment:
```bash

python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows
```

3. Install dependencies:
```bash

    pip install -r requirements.txt

    Set up configuration:

        Copy .env.template to .env and fill in your API keys

        Copy src/utils/api_keys.py.template to src/utils/api_keys.py and fill in

##Usage:

To run the complete pipeline:
```bash

python main.py
```
To run individual modules:
```bash

python -m src.ingestion_engine.ingestion
```
# or
```
python -m src.script_generator.script_gen
```
