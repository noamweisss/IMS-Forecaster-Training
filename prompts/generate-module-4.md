# Handoff prompt — Generate Module 4

Copy everything below the line into a fresh agent session opened on this
repo. Expected runtime: ~15–20 minutes.

---

I'm handing off generation of **Module 4** — the final module — of the IMS Aviation Weather Forecasting Certification course. Modules 1, 2, and 3 already exist in the repo as worked examples.

## Before you write anything

Read these three files in order:

1. `docs/runbook.md` — the procedure.
2. `docs/lesson_spec.md` — the output contract.
3. `docs/journal.md` — engineering log, especially the 2026-05-19 entries that explain *why* the rules exist (no full-document wrappers, no `var(--xxx)` in SVGs, CSS scoped to `.ims-lesson`).

Skim a couple of existing lesson fragments from Modules 1–3 so you've got the target shape internalized before you start writing.

## Module 4 specifics

- **Title:** *Aviation Forecast Products & Warnings*
- **Source files:** numbers 15 through 18 in `courses/aviation-weather/source_files/`:
  - `15. TAF Writing.pptx`
  - `16. Tropical Storms.pptx`
  - `17. Volcanic Ash.pptx`
  - `18. WAFC Maps.pptx`
- **Audience:** Same as the rest of the course — professional meteorologists at IMS seeking Aviation Forecaster certification.
- **Output folder:** `courses/aviation-weather/module-4/`
- **Lesson count:** 4–5 lessons. TAF Writing is the heaviest topic and may merit being split into "TAF structure & format" and "Operational TAF amendments / edge cases" if the source content supports it. Tropical Storms, Volcanic Ash, and WAFC Maps each map naturally to one lesson.

Note: the module title says "Warnings", which overlaps thematically with Module 3 (Area / Aerodrome Warnings). They aren't duplicates — Module 3 is about local warning *systems* and ICAO-required content; Module 4 is about specific *products* (TAFs) and global *hazards* (tropical storms, volcanic ash) plus the global forecast charts (WAFC). If you notice meaningful overlap with content you'd expect Module 3 to cover, flag it in your final report and let the SME resolve it.

## Step-by-step

### Phase 1 — Subdivide and extract

```
mkdir courses/aviation-weather/source_files/module-4
```

Move sources 15, 16, 17, 18 into that subfolder. Then:

```
python pipeline/extract_sources.py \
    --input  courses/aviation-weather/source_files/module-4 \
    --output courses/aviation-weather/module-4/_extraction.json
```

### Phase 2 — Design and author

Following `docs/lesson_spec.md`, produce:

- `courses/aviation-weather/module-4/module_structure.json`
- `courses/aviation-weather/module-4/00_module_overview_moodle.html`
- `courses/aviation-weather/module-4/lessons/NN_<slug>_moodle.html` per lesson
- `courses/aviation-weather/module-4/lessons/NN_<slug>_quiz.xml` per lesson

TAF Writing is dense and code-heavy. Use plenty of annotated SVG diagrams — a worked TAF example with each group color-coded and labeled is exactly the kind of visual that earns its place. Tropical Storms benefits from a track-forecast diagram (cone of uncertainty). Volcanic Ash should include the SIGMET dispersion-area sketch. WAFC Maps merits one or two annotated mock-WAFC-chart SVGs.

The two biggest gotchas: forgetting the leading `<style>` block in each fragment, and writing `fill="var(--accent)"` inside an SVG attribute. The spec doc has the literal hex palette — copy from there.

### Phase 3 — Finalize

```
python pipeline/finalize_module.py --module courses/aviation-weather/module-4
```

### Phase 4 — Images

Things you might legitimately need to flag with `<div class="image-needed" ...>` for this module:

- Photograph of volcanic ash plume from a real eruption (good real-world context).
- Satellite image of a tropical storm (e.g., a Mediterranean storm relevant to IMS forecasting if you can identify one in the source material).

Most other content can be drawn as SVG. If you flag anything, `finalize_module.py` will list it in the module's `IMAGES_TO_SOURCE.md`.

## When you're done

Report back with:
1. Lesson titles.
2. Total quiz question count.
3. Combined-page file size.
4. Anything in `IMAGES_TO_SOURCE.md` (or "none flagged" if empty).
5. Any apparent overlap with Module 3 you noticed.
