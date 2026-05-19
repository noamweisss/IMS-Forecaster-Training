# Handoff prompt — Generate Module 3

Copy everything below the line into a fresh agent session opened on this
repo. Expected runtime: ~10–15 minutes (smaller module than 2 or 4).

---

I'm handing off generation of **Module 3** of the IMS Aviation Weather Forecasting Certification course. Modules 1 and 2 already exist in the repo as worked examples.

## Before you write anything

Read these three files in order:

1. `docs/runbook.md` — the procedure you'll follow.
2. `docs/lesson_spec.md` — the output contract.
3. `docs/journal.md` — engineering log, especially the 2026-05-19 entries that explain *why* the rules exist (no full-document wrappers, no `var(--xxx)` in SVGs, CSS scoped to `.ims-lesson`).

Skim `courses/aviation-weather/module-2/lessons/01_*_moodle.html` (or Module 1 if Module 2 isn't there yet) to see what good output looks like.

## Module 3 specifics

- **Title:** *Terminal Area Hazards & Visibility*
- **Source files:** numbers 13 and 14 in `courses/aviation-weather/source_files/`:
  - `13. Area Warnings.pptx`
  - `14. Aerodrome Warnings.pptx`
- **Audience:** Same as the rest of the course — professional meteorologists at IMS seeking Aviation Forecaster certification.
- **Output folder:** `courses/aviation-weather/module-3/`
- **Lesson count:** This is a small module. 2–3 lessons is appropriate. Don't pad — short modules are fine, and the SME will rearrange if needed.

Note: the module *title* mentions "Visibility", but the source files are about Area Warnings and Aerodrome Warnings specifically. The visibility/fog topics are actually in Module 2 (the grouping doesn't perfectly match the title). Treat the title as a thematic umbrella and build lessons around what the sources actually contain — warnings systems, when they're issued, ICAO-required content. Evgeny will rename the module after review if he wants to.

## Step-by-step

### Phase 1 — Subdivide and extract

```
mkdir courses/aviation-weather/source_files/module-3
```

Move sources 13 and 14 into that subfolder. Then:

```
python pipeline/extract_sources.py \
    --input  courses/aviation-weather/source_files/module-3 \
    --output courses/aviation-weather/module-3/_extraction.json
```

### Phase 2 — Design and author

Following `docs/lesson_spec.md`, produce:

- `courses/aviation-weather/module-3/module_structure.json`
- `courses/aviation-weather/module-3/00_module_overview_moodle.html`
- `courses/aviation-weather/module-3/lessons/NN_<slug>_moodle.html` per lesson
- `courses/aviation-weather/module-3/lessons/NN_<slug>_quiz.xml` per lesson

The two biggest gotchas: forgetting the leading `<style>` block in each fragment, and writing `fill="var(--accent)"` inside an SVG attribute. The spec doc has the literal hex palette — copy from there.

### Phase 3 — Finalize

```
python pipeline/finalize_module.py --module courses/aviation-weather/module-3
```

### Phase 4 — Images

Most warnings content can be diagrammed (timing flowcharts, ICAO-required-content tables, decision trees for when to issue what). Reserve `image-needed` placeholders only for things you genuinely can't draw — e.g. specific real-world warning examples. If you flag anything, `finalize_module.py` will list it in the module's `IMAGES_TO_SOURCE.md`.

## When you're done

Report back with:
1. Lesson titles.
2. Total quiz question count.
3. Combined-page file size.
4. Anything in `IMAGES_TO_SOURCE.md` (or "none flagged" if empty).
