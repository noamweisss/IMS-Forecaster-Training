# IMS Forecaster Training System

A Python pipeline that converts meteorological training presentations (PowerPoint, PDF, Word) into **Moodle-ready HTML lessons and quiz XML files** using the Claude API.

Built for the **Israeli Meteorological Service (IMS)** Aviation Weather Forecasting Certification course.

## What It Does

```
Source presentations (PPTX/PDF/DOCX)
        ↓
   Claude API (4 pipeline stages)
        ↓
HTML lessons + Moodle XML quizzes
```

The pipeline reads your source material, uses AI to design a lesson structure, generates professional HTML lesson pages with inline SVG diagrams, and outputs quiz files in Moodle's import format.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

<!--
### 2. Set up your API key

```bash
cp .env.example .env
# Edit .env and paste your Anthropic API key
```
-->

### 3. Run the pipeline

```bash
python pipeline/module_pipeline.py \
    --input   courses/aviation-weather/source_files \
    --name    "Aviation Weather Fundamentals & Regulations" \
    --number  1 \
    --course  "Aviation Weather Forecasting Certification" \
    --audience "Professional meteorologists seeking Aviation Forecaster certification (IMS)" \
    --output  courses/aviation-weather/module-1
```

## Project Structure

```
├── pipeline/                Python pipeline scripts
│   ├── module_pipeline.py   Main pipeline (extract → blueprint → generate → assemble)
│   ├── embed_images.py      Inlines sourced photos as base64 data URIs in Moodle fragments
│   └── retrofit_to_moodle.py  Converts legacy module HTML to the Moodle-ready format
│
├── prompts/                 Prompt templates for Claude API
├── courses/                 Course content (sources + outputs)
├── config/                  Shared CSS design system
├── admin/                   Moodle admin notes
├── docs/                    Architecture documentation
└── .ai/skills/              AI agent skill files
```

## Course Status

| Module | Topic | Status |
|--------|-------|--------|
| 1 | Aviation Weather Fundamentals & Regulations | ✅ Complete |
| 2 | In-flight Aviation Hazards | 🚧 Planned |
| 3 | Terminal Area Hazards & Visibility | 🚧 Planned |
| 4 | Aviation Forecast Products & Warnings | 🚧 Planned |

## Requirements

- Python 3.10+
- Anthropic API key (Claude)
- See `requirements.txt` for Python packages

## License

Internal IMS project — not for public distribution.
