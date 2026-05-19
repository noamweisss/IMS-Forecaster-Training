# IMS Forecaster Training System

An agent-driven pipeline that converts meteorological training presentations (PowerPoint, PDF, Word) into **Moodle-ready HTML lessons and quiz XML files**.

Built for the **Israeli Meteorological Service (IMS)** Aviation Weather Forecasting Certification course.

## What It Does

```
Source presentations  →  [Python: extract]  →  _extraction.json
                                              ↓
                          [Agent: design + author]
                                              ↓
                       lesson HTML fragments + quiz XML + overview
                                              ↓
                          [Python: finalize]  →  Moodle-ready module
```

A Claude Code agent (using whatever model your IDE provides — no API key needed) reads the extracted source content, designs a lesson structure, and writes each lesson as an HTML body fragment plus its quiz questions. Python scripts handle the boring parts before and after: parsing binary PPTX/PDF/DOCX files, embedding sourced photos, building the combined Moodle page.

See [docs/runbook.md](docs/runbook.md) for the step-by-step procedure when starting a new course or module.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Extract source content

```bash
python pipeline/extract_sources.py \
    --input  courses/<course>/source_files/module-N \
    --output courses/<course>/module-N/_extraction.json
```

### 3. Have an agent generate the lessons

Open this repo in your IDE, start a Claude Code agent, and point it at:
- the extraction JSON from step 2
- the lesson-output spec in [docs/lesson_spec.md](docs/lesson_spec.md)
- the runbook in [docs/runbook.md](docs/runbook.md)

The agent writes lesson HTML fragments, quiz XML files, and the module overview into the module folder.

### 4. Finalize for Moodle

```bash
python pipeline/finalize_module.py --module courses/<course>/module-N
```

This embeds local images as base64, builds the combined Moodle page, writes the upload instructions, and you're ready to paste into Moodle (see the module's `README.md`).

## Project Structure

```
├── pipeline/                  Python scripts (no LLM in any of these)
│   ├── extract_sources.py     PPTX/PDF/DOCX → JSON
│   ├── finalize_module.py     Orchestrates the post-agent steps
│   ├── embed_images.py        Inlines sourced photos as base64 data URIs
│   ├── build_combined_page.py Concatenates lesson fragments into one Moodle Page
│   └── retrofit_to_moodle.py  Converts legacy standalone HTML to fragments
│
├── docs/
│   ├── lesson_spec.md         What the agent should produce per lesson
│   ├── runbook.md             Step-by-step workflow for generating a module
│   ├── journal.md             Engineering log (decisions, dead-ends)
│   └── architecture.md        High-level pipeline overview
│
├── courses/                   Course content (sources + outputs)
├── config/                    Shared CSS design system (.ims-lesson scoped)
├── admin/                     Moodle setup notes, Docker config
├── CHANGELOG.md               Keep-a-changelog log of behavior changes
└── .ai/skills/                AI agent skill files
```

## Course Status

| Module | Topic | Status |
|--------|-------|--------|
| 1 | Aviation Weather Fundamentals & Regulations | ✅ Generated, retrofitted, uploaded |
| 2 | In-flight Aviation Hazards | 🚧 Pending (sources 05–12) |
| 3 | Terminal Area Hazards & Visibility | 🚧 Pending (sources 13–14) |
| 4 | Aviation Forecast Products & Warnings | 🚧 Pending (sources 15–18) |

## Requirements

- Python 3.10+
- See `requirements.txt` for Python packages.
- **No API key required.** The LLM stage runs inside your IDE using whatever model it provides (Claude Code with a Claude subscription, Antigravity with bundled Gemini, etc.).

## License

Internal IMS project — not for public distribution.
