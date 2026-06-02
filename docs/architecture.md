# Pipeline Architecture

The IMS Course Factory converts raw educational materials (PowerPoint, PDF,
Word) into Moodle-ready learning modules. The pipeline is split into three
phases, with the LLM-bound work in the middle done by an agent inside the
user's IDE — there is no API key in the loop.

```
Source files (PPTX/PDF/DOCX)
        │
        ▼
[1] extract_sources.py        ← Python only, no LLM
        │  _extraction.json
        ▼
[2] Claude Code agent         ← LLM, runs inside the IDE
        │  lesson HTML fragments, quiz XMLs, module overview, blueprint
        ▼
[3] finalize_module.py        ← Python only, no LLM
        │  module_combined_moodle.html, module_quiz_all_questions.xml,
        │  IMAGES_TO_SOURCE.md, README.md
        ▼
[4] build_mbz.py (optional)   ← Python only, no LLM
        │  <course>.mbz  (one importable Moodle backup)
        ▼
Moodle (1 restore for the whole course, or 2 clicks per module)
```

## Pipeline Phases

### Phase 1 — Extraction (Python)

`pipeline/extract_sources.py` reads PPTX/PDF/DOCX files and emits a JSON
dump containing every slide's title, bullet points, speaker notes, page
text, and section structure. Single deterministic operation, no model
involved. The output JSON is what the agent reads next — no agent
opens a .pptx directly.

### Phase 2 — Authoring (Agent)

An agent reads `_extraction.json` plus the course context, then writes:

- `module_structure.json` — the blueprint (3–6 lessons, objectives, key
  concepts, visual needs, quiz plan).
- `00_module_overview_moodle.html` — module overview body fragment.
- `lessons/NN_<slug>_moodle.html` — each lesson as a body fragment with
  inline SVG diagrams and callouts.
- `lessons/NN_<slug>_quiz.xml` — each lesson's quiz in Moodle XML format.

The contract for what the agent must produce is in
[lesson_spec.md](lesson_spec.md). The agent operates entirely inside
the user's IDE using whatever model is bundled with their subscription
(Claude Code → Claude, Antigravity → Gemini, etc.).

### Phase 3 — Finalization (Python)

`pipeline/finalize_module.py` orchestrates four sub-steps:

1. Combine per-lesson quiz XMLs into `module_quiz_all_questions.xml`.
2. Embed local images as base64 data URIs (resized + JPEG-recompressed
   via Pillow when available) — via `embed_images.py`.
3. Build `module_combined_moodle.html` by concatenating the overview +
   every lesson fragment, deduping the `<style>` block, and adding an
   in-page table of contents — via `build_combined_page.py`.
4. Write a templated `README.md` with the 2-click upload steps, and
   regenerate `IMAGES_TO_SOURCE.md` from any remaining `image-needed`
   placeholders.

Idempotent. Re-running picks up newly-sourced images or regenerated
lessons without manual intervention.

### Phase 4 — Backup packaging (Python, optional)

`pipeline/build_mbz.py` turns the finalized content into a single importable
Moodle backup (`.mbz`). Restoring it stands up the whole course in one upload:
one section per module, laid out as overview Page → (lesson Page → lesson Quiz)
per lesson, with questions, base64-embedded images, and feedback wired in. Pure
stdlib Python, targeting Moodle 5.2+ (`backup_version 2026042000`). The schema is
documented in [mbz_format.md](mbz_format.md); the `pipeline/mbz/` package splits
the work into ids, quiz conversion, activity builders, structural assembly, and
packaging. The copy-paste outputs from Phase 3 remain as a fallback.

## Design Constraints Driving the Architecture

- **No API key.** The owner uses IDE-bundled inference; the pipeline
  must work without `ANTHROPIC_API_KEY` set.
- **Moodle is a hostile host.** The HTML editor strips full document
  wrappers and sometimes filters `<style>` blocks. Therefore: body
  fragments only, CSS scoped to a `.ims-lesson` wrapper, SVG attributes
  use literal hex colors, images embedded as base64.
- **Two-click upload.** The combined HTML page and the quiz XML are
  the only two things the user touches in Moodle's UI.
- **Course-agnostic.** Nothing in the Python scripts knows about
  "Aviation"; per-course concerns live in `courses/<course>/`.
- **Skill-ready.** The phase split — Python tools + spec doc + worked
  example — maps directly onto a Claude skill's tools + instructions +
  example. Repackaging later is mostly copy-paste.

## Where to Look for Details

- Step-by-step procedure → [runbook.md](runbook.md)
- Output contract → [lesson_spec.md](lesson_spec.md)
- Decision history → [journal.md](journal.md)
- Behavior log → [../CHANGELOG.md](../CHANGELOG.md)
