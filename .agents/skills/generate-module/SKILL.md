---
name: generate-module
description: Build a Moodle-ready training module by extracting source presentations (PPTX, PDF, DOCX) and authoring lesson HTML fragments + quiz XML. Use this skill whenever the user asks to generate, build, author, or write a module, lesson, or quiz inside the IMS Course Factory repo — including phrases like "generate Module 2", "turn these presentations into lessons", "write the quiz for this lesson", "convert this to Moodle", "make a course out of these slides", or anything that involves producing files under `courses/<course>/module-N/`. Also use this when the user points at an `_extraction.json` file and asks for lessons, or when they hand over a folder of slides and ask to turn them into training content. The skill is course-agnostic — Aviation Weather is the worked example, but the same workflow applies to any future course in this repo.
---

# Generate Module

A skill for converting source presentations into a Moodle-ready training module. Built for the Israeli Meteorological Service Course Factory, but course-agnostic — works for any course whose sources live under `courses/<course>/source_files/`.

## What you are doing

Three phases. You run two commands and write the middle phase yourself.

```
1. pipeline/extract_sources.py   →  _extraction.json          (Python, no LLM)
2. you, the agent                →  lesson HTML + quiz XML + overview
3. pipeline/finalize_module.py   →  Moodle-ready module       (Python, no LLM)
```

The audience for the lessons is **certified professional meteorologists** taking a certification refresh course. They are technically literate, time-pressured, and will be irritated by filler prose or condescending explanations. No "in this lesson we will learn…" openers. No basics that a working forecaster already has internalized.

## Before you write a single lesson

Three files to read in full. They are the contract — your output is judged against them, not against this skill's body.

| File | Why |
|------|-----|
| `docs/lesson_spec.md` | The exact shape of every file you produce: output format, required HTML structure, SVG color palette, quiz XML schema, file naming, common mistakes. **Read this in full before phase 2.** |
| `references/lesson_template.html` (in this skill folder) | A complete worked example of a lesson body fragment. Copy this as your starting point for each lesson and replace the content. |
| `references/quiz_template.xml` (in this skill folder) | A complete worked example of a quiz file with proper CDATA wrapping and rationale feedback. |

Also keep at hand: `config/design_system.css` — its full contents go verbatim into every lesson fragment's leading `<style>` block. The lesson template has a marker comment showing exactly where.

## Phase 1 — Extract source content

```bash
python pipeline/extract_sources.py \
    --input  courses/<course>/source_files/module-N \
    --output courses/<course>/module-N/_extraction.json
```

Reads every PPTX/PDF/DOCX in the input folder and writes a JSON dump of slide titles, body text, speaker notes, page text, and section headings. No LLM, just file parsing.

If the source files are not yet split into per-module subfolders, do that first. The groupings come from the course config (e.g., `courses/aviation-weather/course.json`) or from the user. Don't guess — the subject-matter expert decided the groupings on purpose.

After extracting, open `_extraction.json` and actually read it. It is your only source of truth for what content the lessons must cover. Speaker notes often contain the real teaching content while slides only carry headlines — don't skim past them.

## Phase 2 — Design and author

This is the bulk of your work. Five sub-steps.

### 2a. Read the source material carefully

Note for each source file:
- The conceptual groupings (a source often covers several sub-topics; sometimes two sources cover one).
- The depth of treatment — some topics get a single slide, others fifteen. Match your lesson depth to that.
- The speaker notes — most of the real explanation lives there, not on the slides.

### 2b. Design the module structure

Write `courses/<course>/module-N/module_structure.json`. The exact JSON shape is in `docs/lesson_spec.md` under "Module structure". The blueprint determines lesson count, ordering, and learning objectives. Key rules:

- **3–6 lessons per module.** Each lesson is roughly 20 minutes of self-paced study.
- **Learning objectives must be testable** — they map directly to quiz questions. "Understand X" is not testable. "Calculate Y given Z" is. Use Bloom's-taxonomy action verbs (identify, calculate, distinguish, predict).
- For each lesson, flag visuals you'll need that can't be inline SVG (real photographs, satellite imagery). These become `image-needed` placeholders the user fills in later.

Show the blueprint to the user before writing any lessons. Iterating on lesson count and objectives is cheap; iterating after writing five lessons is not.

### 2c. Write each lesson body fragment

For each lesson, create `courses/<course>/module-N/lessons/NN_<slug>_moodle.html` starting from `references/lesson_template.html`. The template shows the required outer structure: leading `<style>` block, `<div class="ims-lesson">` wrapper, breadcrumb, h1, objectives, content sections, summary.

Fill the body with:
- **Prose** broken into short paragraphs (2–4 sentences each).
- **`<h2>` and `<h3>` headings** for navigation.
- **Tables** for comparisons. The design system styles them — just write semantic HTML.
- **Inline SVG diagrams** for relationships, hierarchies, sequences, and comparisons that prose can't carry. Aim for roughly one visual per 200–300 words.
- **Callouts** for definitions, warnings, key formulas, danger cases. Four classes: `callout-note`, `callout-warning`, `callout-key`, `callout-danger`.
- **`<div class="image-needed" data-description="...">`** for real photographs to be sourced later. The `data-description` text becomes the entry in `IMAGES_TO_SOURCE.md`, so be specific about what the photo should show.
- **Summary** at the bottom: 4–6 takeaway bullets.

The non-negotiable constraints (the rest are in `lesson_spec.md`):

- **Body fragments only.** No `<!DOCTYPE>`, `<html>`, `<head>`, `<body>` wrappers. The fragment starts with `<style>` and ends with `</div>`. A full HTML document gets stripped by Moodle's editor and the lesson renders as raw text.
- **Literal hex colors in every SVG attribute.** Never `fill="var(--accent)"` — always `fill="#185FA5"`. Moodle strips or re-scopes the `<style>` block unpredictably, and SVG attributes that reference CSS variables fall back to invisible defaults. The palette is in `lesson_spec.md` under "SVG rules". This rule is the single most common failure mode of the pipeline; it caused the entire retrofit work documented in `docs/journal.md`.
- **The CSS goes inside the fragment, scoped to `.ims-lesson`.** Copy `config/design_system.css` verbatim into the leading `<style>` block. Don't modify the selectors. The scoping is what stops Moodle's own theme from fighting our typography.
- **No filler.** Start with content. The audience is professional.

### 2d. Write each lesson's quiz

For each lesson, create `courses/<course>/module-N/lessons/NN_<slug>_quiz.xml` starting from `references/quiz_template.xml`. Moodle XML question bank format, one file per lesson. The finalize step will merge them.

Quality bar:

- **4–8 questions per lesson**, roughly one per 4 minutes of lesson content.
- **Exactly 4 answer options per question, all plausible.** Wrong answers should reflect real misconceptions a working forecaster might have — not obvious filler. If you can't think of a plausible fourth distractor, the question is probably testing something too narrow.
- **Application-level, not recall.** "What is the ICAO acronym for X?" is recall and is wrong for this audience. "Given conditions A, B, and C, which procedure applies?" is application. Use scenarios.
- **Always fill in `<generalfeedback>`.** This is the rationale the student sees after answering, and it is where the actual learning happens. Explain why the correct answer is right and (briefly) why the most tempting distractor is wrong. Treat it as the highest-value text in the entire quiz.
- **CDATA-wrap all HTML** inside `<text>` elements. The template shows the exact pattern.

### 2e. Write the module overview

Create `courses/<course>/module-N/00_module_overview_moodle.html`. Same outer structure as a lesson, content is module-level: title, duration estimate, lesson count, the certification competencies (from `module_structure.json`), and one summary card per lesson. The exact template is in `lesson_spec.md` under "Module overview body".

The summary cards in the overview use inline styles with literal hex (not class-based styling) so they survive even if Moodle strips the leading `<style>` block. The template in the spec shows the exact markup.

## Phase 3 — Finalize

```bash
python pipeline/finalize_module.py --module courses/<course>/module-N
```

This:
- Combines the per-lesson quiz XMLs into `module_quiz_all_questions.xml`.
- Embeds any locally-saved images (under `lessons/Images/`) as base64 data URIs.
- Builds `module_combined_moodle.html` — the single-paste-into-Moodle file with sticky table of contents.
- Regenerates `IMAGES_TO_SOURCE.md` from any `image-needed` placeholders still present.
- Writes `README.md` with the 2-click Moodle upload steps.

Idempotent. If the user later sources photos for the `image-needed` placeholders and edits the lesson HTML to reference them, re-run finalize and the new images get embedded.

## Sanity checks before declaring done

Five-minute self-review of your output. Catches the failure modes the journal documents:

1. **No CSS variables inside SVGs.**
   ```bash
   grep -nE 'fill="var\(|stroke="var\(' courses/<course>/module-N/lessons/*_moodle.html
   ```
   Should return nothing. If it does, the diagrams will be invisible in Moodle.

2. **No HTML-document wrappers.**
   ```bash
   grep -lE '<!DOCTYPE|<html|<head>|<body>' courses/<course>/module-N/lessons/*_moodle.html courses/<course>/module-N/00_module_overview_moodle.html
   ```
   Should return nothing. Body fragments only.

3. **One lesson opens cleanly in a browser as a standalone file.** Open any `NN_<slug>_moodle.html` directly. It should render with full styling because the leading `<style>` block is self-sufficient.

4. **One quiz XML parses.**
   ```bash
   python -c "import xml.etree.ElementTree as ET; ET.parse('courses/<course>/module-N/lessons/01_<slug>_quiz.xml')"
   ```
   If it parses without error the XML is well-formed. If not, look for unbalanced CDATA or missing `<answer>` blocks.

5. **The overview lists every lesson.** Open `00_module_overview_moodle.html` and count the summary cards against the lesson files in `lessons/`.

## When to ask the user vs. when to proceed

**Ask before writing lessons:**
- After designing the blueprint (`module_structure.json`) — confirm lesson count, ordering, and objectives.
- If the source content is genuinely ambiguous or sparse for a topic and you'd otherwise be making things up.
- If you're unsure whether a topic belongs in this module or a later one — the subject-matter expert may have intent you can't infer from the slides.

**Proceed without asking:**
- Stylistic choices that conform to the spec (which callout class, exact diagram design, prose phrasing).
- Routine pipeline commands.
- Self-correction after a sanity-check failure.

## Reference files in this skill folder

| File | When to load |
|------|--------------|
| `references/lesson_template.html` | At the start of writing each lesson. Use as scaffolding. |
| `references/quiz_template.xml` | At the start of writing each quiz. Use as scaffolding. |

## Reference files in the repo

| File | When to load |
|------|--------------|
| `docs/lesson_spec.md` | Before phase 2. The full output contract. |
| `docs/runbook.md` | If you want the operational view of the whole pipeline. |
| `docs/journal.md` | If something looks weird and you want the backstory of why a rule exists. |
| `config/design_system.css` | When you're about to embed the CSS in a lesson's leading `<style>` block. |
| `courses/<course>/course.json` | At the start of phase 1, to confirm module groupings and titles. |

## Documenting your work

This repo follows a small documentation convention (see `AGENTS.md`): every meaningful step gets a commit and a paper trail. After finishing a module:

- **Journal entry** in `docs/journal.md` if you made any non-obvious authoring decisions (merged two source files into one lesson, split a source across two, omitted a topic, deviated from the spec for a specific reason). Use the standard Context / Decision / Why structure.
- **Changelog entry** in `CHANGELOG.md` under `## [Unreleased]`, one line: `Generated Module N (<title>) for the <course> course.`
- **Commit each phase separately.** Conventional commit style is fine:
  - `chore: extract sources for module N`
  - `feat: author module N lessons and quizzes`
  - `chore: finalize module N for Moodle`

This makes future review possible and keeps the repo's history readable for the project owner, who is learning the codebase as we build it.
