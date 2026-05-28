# AGENTS.md — IMS Forecaster Training System

## Agent Personality
It is important to remeber that the project owner is NOT a professional developer — they're new to programming and need things explained in simple, clear terms. you need to be patient and informative to make this a good experience for them.
Also, it is crucial that you document everything, both in the journal [docs/journal.md](docs/journal.md) and in the changelog [CHANGELOG.md](CHANGELOG.md) (when relevant.) also, always be committing small logical steps to git. never do any change without comitting and explaining it in clear terms for future examination. 

**Ship documentation incrementally.** Each code commit carries its own
journal/CHANGELOG update for that step. Never batch all the documentation into one
big writeup at the end — the journal should read as a running log, and every
commit should leave the docs true. Small-and-followable beats tidy-on-paper.


## What This Project Is

A pipeline that converts PowerPoint, PDF, and Word presentations into
Moodle-ready HTML lessons and Moodle XML quiz files. Built for the
**Israeli Meteorological Service (IMS)** aviation weather forecasting
certification course; designed to be reusable for any future IMS course.

## How It Actually Works

Three phases. The middle one is the only one that uses an LLM, and it
runs *inside the user's IDE* using whatever model is bundled with their
subscription (Claude via Claude Code, Gemini via Antigravity, etc.).
**No Anthropic API key is required anywhere.**

```
1. extract_sources.py        → _extraction.json     (Python, no LLM)
2. you / another agent        → lesson HTML + quiz XML + overview
3. finalize_module.py         → Moodle-ready module (Python, no LLM)
```

## If You're an Agent Reading This for the First Time

Start here:
- **[docs/runbook.md](docs/runbook.md)** — step-by-step procedure for
  generating a module end to end.
- **[docs/lesson_spec.md](docs/lesson_spec.md)** — the exact files,
  shapes, and conventions you must produce when authoring lessons.
- **[docs/journal.md](docs/journal.md)** — engineering log. Read this
  when something looks weird and you want the backstory.
- **[CHANGELOG.md](CHANGELOG.md)** — what changed recently.

## Key Concepts

- **Module**: A self-contained unit of learning (~90 min). Each module
  has 3–6 lessons.
- **Lesson**: An HTML body fragment scoped to `.ims-lesson`, containing
  prose, inline SVG diagrams, tables, callouts, and a quiz (the quiz
  lives in a sibling XML file).
- **Body fragment vs standalone**: All Moodle-bound output is a body
  fragment (`<style>...</style><div class="ims-lesson">...</div>`)
  with no `<html>`/`<head>`/`<body>` wrappers. Full HTML documents
  are not produced anymore.
- **Source files**: The original presentations (PPTX/PDF/DOCX) in
  Hebrew, already translated to English filenames. See
  `courses/aviation-weather/source_files/file_name_mapping.txt`.

## Project Structure

```
pipeline/           → Python scripts (no LLM in any of them)
  extract_sources.py      PPTX/PDF/DOCX → JSON
  finalize_module.py      Orchestrates the post-LLM Python work
  embed_images.py         Inlines images as base64 (with downscaling)
  build_combined_page.py  Concatenates lesson fragments into one Page
  retrofit_to_moodle.py   Upgrades legacy standalone HTML to fragments

docs/                → Documentation, runbook, spec, journal
courses/             → Course content (source files + generated output)
  aviation-weather/        The pilot course
config/              → Shared CSS design system (.ims-lesson scoped)
admin/               → Moodle setup notes, Docker config
.claude/skills/      → Agent skill files (canonical home). Holds
                       `generate-module/`, the course-conversion skill
                       that packages this pipeline.
.agents/skills/      → Synced mirror of `.claude/skills/` for
                       Antigravity. Keep the two in lockstep.
```

### Skill location convention

The canonical home for agent skills is `.claude/skills/<name>/`, and an
identical copy is kept at `.agents/skills/<name>/`. Both folders exist
because the two tools we use look in different places: Claude Code reads
`.claude/skills/`, while Antigravity reads `.agents/skills/`. The project
owner uses both products roughly equally, so a skill that only lived in
one location would silently fail to load in the other. When editing a
skill, change `.claude/skills/<name>/` and then copy the result over to
`.agents/skills/<name>/` (or vice versa) in the same commit so the mirror
never drifts.

## Tech Stack

- **Python 3.10+** with `python-pptx`, `pymupdf`, `python-docx`, `Pillow`.
- **No LLM SDK is called by any pipeline script.** The agent stage uses
  whatever inference is available in the user's IDE.
- **Output format**: HTML body fragments scoped to `.ims-lesson` +
  Moodle XML question bank format.

## Important Conventions

- All source files have been renamed from Hebrew to English (see
  `courses/aviation-weather/source_files/file_name_mapping.txt`).
- The CSS design system uses CSS custom properties **declared on
  `.ims-lesson`** (not `:root`) so the styles can't leak out into
  Moodle's chrome.
- SVG diagrams are generated inline using **literal hex colors only** —
  `var(--xxx)` inside an SVG attribute is forbidden. The agent is
  responsible for following this rule; there is no post-processing
  scrubber in the new pipeline.
- `<div class="image-needed">` markers flag where real photographs need
  to be sourced manually. `finalize_module.py` extracts them into
  `IMAGES_TO_SOURCE.md`.
- Module output goes in `courses/<course>/module-N/`. The Python
  scripts always operate on a module folder, never on the whole course
  at once.

## Setup

```bash
pip install -r requirements.txt
git lfs install && git lfs pull
```

That's it. No `.env`. No API key. Run `python pipeline/extract_sources.py --help`
to confirm everything is wired up.

> **Claude Code on-the-web sessions:** the sandbox's git proxy doesn't
> serve LFS, so `git lfs pull` fails with `HTTP 502` until you bypass
> it: `apt-get install -y git-lfs && git lfs install --skip-repo &&
> git config lfs.url https://github.com/<owner>/<repo>.git/info/lfs &&
> git lfs pull`. **Before pushing**, undo the override (`git config
> --unset lfs.url && git config lfs.locksverify false`) so push uses
> the proxy. If the source PPTX/PDFs in
> `courses/<course>/source_files/` are ~130 bytes each, that's the
> download-side symptom. See `docs/runbook.md` (Prerequisites) and
> `docs/journal.md` (2026-05-20) for details.

## When the Owner Says "Generate Module N"

Follow the runbook. The condensed version:

1. Subdivide `source_files/` into per-module subfolders if not already.
2. `python pipeline/extract_sources.py --input ... --output ...`
3. Read `docs/lesson_spec.md`. Author the lessons + quizzes + overview.
4. `python pipeline/finalize_module.py --module ...`
5. Tell the user to follow the module's `README.md` for the 2-click
   Moodle upload.
