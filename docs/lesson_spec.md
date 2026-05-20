# Lesson-Output Specification

This document defines exactly what an agent must produce when generating a
module. Companion to [runbook.md](runbook.md) (which describes the *process*).
If you're an agent reading this for the first time, also read
[journal.md](journal.md) for the *why* behind these rules.

## What you produce, per module

```
<module-dir>/
├── 00_module_overview_moodle.html        ← body fragment for Moodle
├── module_structure.json                  ← the blueprint you designed
├── lessons/
│   ├── 01_<slug>_moodle.html             ← body fragment per lesson
│   ├── 01_<slug>_quiz.xml                ← Moodle XML quiz per lesson
│   ├── 02_<slug>_moodle.html
│   ├── 02_<slug>_quiz.xml
│   └── ...
```

Do **not** produce: full standalone HTML pages, `<!DOCTYPE>`, `<html>`,
`<head>`, `<body>`, separate CSS files, image files, README, or a combined
module page. The Python `finalize_module.py` step generates those.

## Audience and tone

- Readers are **certified professional meteorologists** at the Israeli
  Meteorological Service taking a refresh / certification course.
- They are technically literate and time-pressured.
- Authoritative, precise, direct. **No filler.** Skip "In this lesson we will
  learn..." openers. Start with content.
- Don't over-explain basics. Don't condescend.
- A reader should finish a lesson and feel they've gained something
  operational, not been read a textbook chapter.

## Module structure (`module_structure.json`)

```json
{
  "module_title": "...",
  "module_description": "2–3 sentences. What this module covers and why it matters operationally.",
  "estimated_duration_minutes": 90,
  "competencies": [
    "Interpret METAR observations in degraded visibility conditions",
    "..."
  ],
  "lessons": [
    {
      "lesson_id": "L1",
      "lesson_title": "...",
      "learning_objectives": [
        "Verb-led, measurable. Use Bloom's-taxonomy action verbs.",
        "..."
      ],
      "source_files": ["filename.pptx", "other.pdf"],
      "key_concepts": ["TERM_A", "TERM_B"],
      "visual_elements_needed": [
        "Be specific. Not 'a diagram' — 'a flowchart showing the steps from observation to encoded METAR'."
      ],
      "external_imagery_needed": [
        "Photograph of convective cloud development over an airport"
      ],
      "estimated_duration_minutes": 20
    }
  ],
  "module_quiz": {
    "description": "End-of-module summative assessment",
    "question_count": 15,
    "passing_score_percent": 75
  }
}
```

Guidance:
- **3–6 lessons per module** is the sweet spot for ~90 min of self-paced time.
- Learning objectives must be testable. "Understand X" is not testable;
  "Calculate the corrected altitude given temperature deviation X" is.
- For `visual_elements_needed`, describe what the diagram should show
  conceptually — the SVG you draw later must match.
- `external_imagery_needed` is anything you can't draw as an SVG (a real
  photograph, a satellite image). Each entry produces an
  `image-needed` placeholder in the rendered HTML.

## Lesson body fragment (`NN_<slug>_moodle.html`)

Body fragment only. Starts with a `<style>` block, then a wrapper `<div>`.

### Required overall shape

```html
<style>
/* The full design-system CSS, lifted verbatim from config/design_system.css.
   Every rule must be prefixed with .ims-lesson — don't change the scope. */
</style>
<div class="ims-lesson">
<p class="breadcrumb">Module N / Lesson K</p>
<h1>Lesson title</h1>

<div class="objectives">
  <strong>By the end of this lesson you will be able to:</strong>
  <ul>
    <li>... (the learning_objectives from module_structure.json)</li>
  </ul>
</div>

<!-- Lesson content goes here. See sections below. -->

<div class="lesson-summary">
  <h3>Key Takeaways</h3>
  <ul>
    <li>4–6 takeaway bullets summarizing the lesson</li>
  </ul>
</div>
</div>
```

Always include the `<style>` block at the top of every lesson fragment.
`finalize_module.py` does not inject it; it's part of what makes the
fragment self-contained when pasted into Moodle.

The shared CSS lives in [config/design_system.css](../config/design_system.css).
Open it before you start — every class you use comes from there.

### Content sections

Visual-first. A diagram, table, or annotated figure is required roughly
every 200–300 words of prose.

Available building blocks (all classes are scoped to `.ims-lesson`):

| Element | Markup |
|---------|--------|
| Section heading | `<h2>...</h2>` |
| Sub-heading | `<h3>...</h3>` |
| Prose paragraph | `<p>...</p>` (2–4 sentences max) |
| Comparison table | `<table><thead>...<tbody>...</table>` |
| Diagram with caption | `<figure><svg ...>...</svg><figcaption>...</figcaption></figure>` |
| Photo placeholder (for sourcing later) | `<div class="image-needed" data-description="...">📷 Image needed: ...</div>` |
| Note callout | `<div class="callout callout-note">...</div>` |
| Warning callout | `<div class="callout callout-warning">...</div>` |
| Key-formula callout | `<div class="callout callout-key">...</div>` |
| Danger callout | `<div class="callout callout-danger">...</div>` |

### SVG rules — critical

Inline SVGs render inside Moodle Pages where our CSS variables do not
resolve. Every color, fill, and stroke value MUST be a **literal hex
code**. Never `var(--anything)` inside SVG attributes.

Use this palette:

| Token | Hex | Use |
|-------|-----|-----|
| accent blue   | `#185FA5` | primary lines, table headers, emphasis |
| teal          | `#0F6E56` | secondary accent, "note" borders |
| amber         | `#BA7517` | "warning" accents |
| coral         | `#993C1D` | rare emphasis, danger states |
| key purple    | `#534AB7` | "key formula" accents |
| text dark     | `#1A1917` | all SVG text (readable on any background) |
| muted gray    | `#6B6A65` | secondary text, axis labels |
| border gray   | `#E2DFD6` | dividers, weak strokes |
| surface cream | `#F6F5F0` | container fills |
| note bg light | `#E1F5EE` | low-emphasis "note" backgrounds |
| warn bg light | `#FAEEDA` | low-emphasis "warn" backgrounds |
| key bg light  | `#EEEDFE` | low-emphasis "key" backgrounds |

SVG attributes:
- `viewBox="0 0 680 H"` where H fits the content. 680 is the lesson's
  effective content width.
- `role="img"` plus `<title>` and `<desc>` children for accessibility.
- Font: `sans-serif`, 14 px for labels, 12 px for subtitles.
- No gradients. No external image references. No web fonts.
- Never use pure white or pure black as a fill (they fight light/dark mode
  page backgrounds).

If you slip a `var(--xxx)` reference into an SVG attribute,
`pipeline/finalize_module.py` will *not* scrub it. The old API-based
pipeline had a scrubber; the agent-driven flow expects you to be careful.
Re-read your SVG output before saving.

### Image-needed placeholders

For visuals that can't be a generated SVG (real photographs, satellite
imagery, instrument close-ups), emit:

```html
<div class="image-needed" data-description="Close-up photograph of an aircraft altimeter showing the Kollsman window and pressure setting dial.">
  <span>📷 Image needed: Close-up photograph of an aircraft altimeter ...</span>
</div>
```

`finalize_module.py` collects these into `IMAGES_TO_SOURCE.md`. After the
human sources the image and drops it into `lessons/Images/`, they will edit
the placeholder into a real `<img src="images/...">` tag and re-run
`finalize_module.py` to embed it.

### Source-extracted images

`pipeline/extract_sources.py` writes every embedded image it finds in the
source PPTX/PDF/DOCX into `<module>/extracted_images/<source-stem>/` and
indexes them in `_extraction.json`. Per slide / per page:

```json
"images": [
  {
    "path":   "extracted_images/16_Tropical_Storms/slide07_img1.png",
    "format": "png",
    "width":  1920,
    "height": 1080,
    "hash":   "a1b2c3d4"
  }
]
```

`path` is relative to the module directory. From a lesson under
`<module>/lessons/`, reference one with:

```html
<img src="../extracted_images/16_Tropical_Storms/slide07_img1.png"
     alt="Specific description of what the figure shows">
```

Use these only when the source image is a real teaching figure — a
labelled diagram, a satellite snapshot, a forecast chart, a recognisable
instrument photo — and the slide is clearly built around it. Skip
backgrounds, logos, slide chrome, and thumbnails. When unsure, fall back
to an `image-needed` placeholder.

`finalize_module.py` (`embed_images.py`) inlines extracted images as
base64 data URIs at finalize time, the same way it handles
`lessons/Images/` files.

## Quiz XML (`NN_<slug>_quiz.xml`)

Moodle XML question-bank format. One file per lesson. The
`finalize_module.py` script will combine them into one
`module_quiz_all_questions.xml` per module.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>L1-Q01 — Short title</text></name>
    <questiontext format="html">
      <text><![CDATA[<p>Scenario-based question text in HTML.</p>]]></text>
    </questiontext>
    <generalfeedback format="html">
      <text><![CDATA[<p><strong>Rationale:</strong> Why the correct answer is right.</p>]]></text>
    </generalfeedback>
    <defaultgrade>1</defaultgrade>
    <single>true</single>
    <shuffleanswers>true</shuffleanswers>
    <answer fraction="100" format="html">
      <text><![CDATA[<p>Correct answer text.</p>]]></text>
      <feedback format="html"><text></text></feedback>
    </answer>
    <answer fraction="0" format="html">
      <text><![CDATA[<p>Plausible wrong answer.</p>]]></text>
      <feedback format="html"><text></text></feedback>
    </answer>
    <!-- two more wrong answers -->
  </question>
  <!-- more questions -->
</quiz>
```

Rules:
- **Application-level questions**, not recall. Use scenarios. "Given X
  conditions, which of these is the correct procedure?"
- Exactly **4 options per question**. All 4 plausible — wrong answers
  should reflect real misconceptions a forecaster might have.
- `fraction="100"` for the correct answer; `fraction="0"` for the rest.
- `generalfeedback` is the rationale that appears after answering. Always
  fill it in — explain *why* the correct answer is right and (briefly)
  why the most tempting distractor is wrong.
- `<name>` is a short internal label that helps when reviewing in Moodle.
  Format: `L<lesson_id>-Q<NN> — short title`.
- 4–8 questions per lesson, roughly proportional to lesson duration
  (~1 question per 4 minutes).

## File naming

- Lesson slug: derived from the lesson title — lowercase, words joined
  by underscores, no special characters, max 60 characters.
  Example title "International Regulatory Frameworks (WMO & ICAO)" →
  slug `international_regulatory_frameworks`.
- Lesson HTML: `NN_<slug>_moodle.html` where `NN` is zero-padded lesson
  index (`01`, `02`, ...).
- Lesson quiz: `NN_<slug>_quiz.xml`.
- Overview: `00_module_overview_moodle.html` (zero-prefix to sort first).

## Module overview body

The overview is its own body fragment in `00_module_overview_moodle.html`.
Same outer wrapping as a lesson. Content:

```html
<div class="ims-lesson">
<p class="breadcrumb">Module N overview</p>
<h1>{module_title}</h1>

<p class="meta">
  Estimated duration: ~{X} min &nbsp;|&nbsp;
  {N} lessons &nbsp;|&nbsp;
  Module quiz: {Q} questions, pass at 75%
</p>

<p>{module_description from module_structure.json}</p>

<div class="objectives">
  <strong>By completing this module you will be certified to:</strong>
  <ul>
    <!-- one <li> per competency -->
  </ul>
</div>

<h2>Lessons</h2>

<div style="border:1px solid #E2DFD6; border-radius:8px; padding:1rem 1.25rem; margin:0.75rem 0;">
  <div style="display:flex; justify-content:space-between; align-items:baseline;">
    <strong>Lesson 1: {lesson title}</strong>
    <span style="color:#6B6A65; font-size:0.85rem;">~{X} min</span>
  </div>
  <ul style="margin:0.5rem 0 0; padding-left:1.4rem; font-size:0.9rem;">
    <!-- learning_objectives as <li>s -->
  </ul>
</div>
<!-- one block per lesson -->
</div>
```

Note: the lesson summary cards above use *inline styles with literal hex
colors* rather than `var(--xxx)`, so they survive when Moodle strips the
`<style>` block. The lesson body itself uses class-based styling.

## Common mistakes to avoid

- **Wrapping in `<!DOCTYPE>` / `<html>` / `<body>`.** Forbidden. Body
  fragment only.
- **Forgetting the leading `<style>` block.** Without it, the fragment
  loses all callout/table/typography styling in Moodle.
- **`var(--xxx)` inside an SVG.** Will render as black or invisible in
  Moodle.
- **Generic learning objectives** ("Understand X", "Be aware of Y"). Not
  testable, not measurable.
- **Recall-only quiz questions.** "What is the ICAO acronym for X?" Bad.
  Aim for application: scenario → decision → which is correct.
- **One giant paragraph.** Break it up. 2–4 sentences per `<p>`.
- **Diagrams that are just labeled boxes.** A diagram earns its place by
  showing a relationship the prose can't easily describe — sequence,
  hierarchy, comparison, cause-effect.
