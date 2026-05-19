# AGENTS.md — IMS Forecaster Training System

> **⚠️ The project owner is NOT a professional developer — they're new to programming and need things explained in simple, clear terms.**

## What This Project Is

A Python pipeline ("Course Factory") that converts PowerPoint, PDF, and Word presentations into Moodle-ready HTML lessons and Moodle XML quiz files. Built for the **Israeli Meteorological Service (IMS)** aviation weather forecasting certification course.

## Key Concepts

- **Module**: A self-contained unit of learning (~90 min). Each module has 3–6 lessons.
- **Lesson**: An HTML page with inline SVG diagrams, tables, callouts, and a quiz.
- **Pipeline**: The Python code that reads source files → calls Claude API → writes output files.
- **Source files**: The original presentations (PPTX/PDF/DOCX) in Hebrew, already translated to English filenames.

## Project Structure

```
pipeline/           → Python scripts (the pipeline code)
prompts/            → Markdown prompt templates for Claude API calls
courses/            → Course content (source files + generated output)
  aviation-weather/ → The IMS aviation weather certification course
config/             → Shared CSS and design tokens
admin/              → Moodle setup notes, Docker config
docs/               → Architecture docs, design decisions
.ai/skills/         → Step-by-step instructions for AI agents
```

## How the Pipeline Works

1. **Extract** — Read all PPTX/PDF/DOCX files, pull out text, titles, bullet points, speaker notes
2. **Blueprint** — Send summaries to Claude, get back a lesson structure (JSON)
3. **Generate** — Send each lesson's source content to Claude, get back HTML + quiz questions (parallel)
4. **Assemble** — Write HTML lesson files, Moodle XML quiz files, overview page, README

## Tech Stack

- **Python 3.10+** with `anthropic`, `python-pptx`, `pymupdf`, `python-docx`
- **Claude API** (Anthropic) — model: `claude-sonnet-4-20250514`
- **Output format**: Standalone HTML (no framework, inline CSS) + Moodle XML

## Important Conventions

- All source files have been renamed from Hebrew to English (see `file_name_mapping.txt`)
- The CSS design system uses CSS custom properties with automatic dark mode
- SVG diagrams are generated inline (no external files) — flat colors, dark-mode safe
- `<div class="image-needed">` markers flag where real photographs need to be sourced manually

## Environment Setup

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and add your Anthropic API key
3. Run: `python pipeline/module_pipeline.py --help`
