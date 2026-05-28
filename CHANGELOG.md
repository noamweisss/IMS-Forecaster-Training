# Changelog

All notable changes to the IMS Forecaster Training System pipeline are documented
here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Dates are in YYYY-MM-DD.

The companion [engineering journal](docs/journal.md) records the *why* behind
each change — decisions, dead-ends, lessons learned. New developers (and the
future course-to-mbz Claude skill) should read both.

## [Unreleased]

### Added
- **`pipeline/build_mbz.py` — one-upload Moodle course backup:** New pipeline
  step that turns finalized course content into a single importable `.mbz`.
  Restoring it stands up the whole course in one upload: one section per module,
  laid out as overview Page → (lesson Page → lesson Quiz) per lesson, with all
  questions, base64-embedded images, and feedback wired in. Pure stdlib Python.
  First full build of the Aviation Weather course: 1.4 MB, 5 sections, 40
  activities, 82 questions; structural cross-references verified. Generated
  `.mbz` files are gitignored (`courses/**/*.mbz`) — regenerate with
  `python pipeline/build_mbz.py --course courses/<course>`.
  - `--module <folder>` builds a single-module `.mbz`; `finalize_module.py --mbz`
    builds it as part of finalizing.

### Changed
- **Docs** updated for the `.mbz` path: `docs/runbook.md` Phase 6 (restore as
  Option A, copy-paste as fallback), `docs/architecture.md` (Phase 4),
  `AGENTS.md` (pipeline diagram, structure, steps), and the per-module
  `README.md` template.
- **New `prompts/restore-mbz-to-moodle.md`** — step-by-step restore walkthrough
  (build → Course → Restore → Merge), with spot-checks and troubleshooting.
- **`courses/aviation-weather/course.json`** module statuses refreshed — all four
  modules generated, finalized, and packaged into the course `.mbz` (the prior
  "Pending generation" entries for modules 2 and 4 were stale).

> Note: the `.mbz` output is verified structurally (well-formed XML, resolved
> cross-references). A real restore into a live Moodle 5.2 instance is the
> remaining acceptance test before this is considered done.
- **`.mbz` structural assembler:** `pipeline/mbz/structure.py` builds the
  `moodle_backup.xml` manifest, section files (with cmid sequences), the course
  record + boilerplate, the course `gradebook.xml`, and the full `questions.xml`
  question bank — wiring each quiz to its questions through shared contextids.
- **`.mbz` per-activity builders:** `pipeline/mbz/activities.py` builds a full
  Page or Quiz activity directory (`module.xml`, `page.xml`/`quiz.xml`, grades,
  inforef, and boilerplate). The quiz links to its questions via the modern
  question-bank-entry model and carries its own grade item.
- **`.mbz` boilerplate + ID allocator:** `pipeline/mbz/templates.py` holds the
  ~20 constant backup XML files (per-activity, course, and top-level boilerplate)
  as reviewable named constants, and `pipeline/mbz/ids.py` provides a
  deterministic per-entity-type id allocator + question-stamp helper. (Boilerplate
  consolidated into one module rather than 20 tiny `.xml` stubs — see journal.)
- **Quiz import→backup converter:** New `pipeline/mbz/quiz_to_backup.py` —
  converts our Moodle-import-format lesson quizzes into the nested backup
  `<question>` format a `.mbz` restore expects (field remaps + escaped HTML).
  Ships with a self-test that converts all 16 module-1 questions and checks
  well-formedness. First building block of the `.mbz` generator.
- **Moodle 5.2 `.mbz` reference + schema map:** Reviving the deferred Moodle
  backup (`.mbz`) generator now that we have a real reference export. Added
  `docs/mbz_reference/` (the raw reference `.mbz` and its extracted XML tree,
  provenance) and `docs/mbz_format.md` (the canonical schema map the builder is
  coded against — version stamps, archive layout, page/quiz/question-bank XML,
  `.ARCHIVE_INDEX`, and the import→backup quiz-field mapping). Target: Moodle
  5.2+ (build 20260501), `backup_version 2026042000`.
- **Incremental-documentation working practice:** Made the repo's "commit small
  logical steps" rule explicit about docs — every code commit carries its own
  journal/CHANGELOG update. Recorded in `AGENTS.md` and the `generate-module`
  skill (both `.claude/` and `.agents/` mirrors).

### Added
- **Course-Wide Preview Compiler:** Added `pipeline/build_course_preview.py` — a reusable, course-agnostic Python pipeline that compiles all generated modules, lessons, inlined SVG diagrams, base64-embedded images, and XML quizzes into a single highly-polished offline-first Single Page App (SPA) `index.html` file in under 2 seconds. Built with pure Python standard libraries (no third-party dependencies) for instant native execution in any CI environment.
- **Git-Synced Netlify Continuous Deployment:** Added a root-level `netlify.toml` configuration to integrate the preview compiler directly with Netlify's continuous deployment. Every `git push` automatically rebuilds the entire course preview and publishes it to the same permanent live demonstration link, allowing seamless feedback-and-revision cycles.

### Added
- **Module 3 generated:** "Aviation Warnings: SIGMET, AIRMET &
  Aerodrome" — 4 lessons (24-question end-of-module quiz) covering the
  three statutory IMS warning products. Title changed from the
  original "Terminal Area Hazards & Visibility" in `course.json`
  because the source decks (13: Area Warnings, 14: Aerodrome Warnings)
  are about warning products, not hazards-as-phenomena.
- **Docs:** Git-LFS workaround for Claude Code on-the-web sandboxes
  (set `lfs.url` to GitHub directly to bypass the local proxy's 502 on
  the LFS batch API). Documented in `AGENTS.md` Setup,
  `docs/runbook.md` Prerequisites + Troubleshooting, and
  `docs/journal.md` with full root-cause analysis.

- **Skill:** New `.claude/skills/generate-module/` (mirrored to
  `.agents/skills/generate-module/`) — packages the
  three-phase course-to-Moodle pipeline as a reusable Claude skill.
  Contains `SKILL.md` (the agent entry point with workflow and
  constraints), `references/lesson_template.html` (worked-example
  lesson body fragment), and `references/quiz_template.xml`
  (worked-example quiz with two application-level questions). The
  skill references (does not duplicate) `docs/lesson_spec.md`,
  `docs/runbook.md`, and `config/design_system.css` so it stays in
  lockstep with the repo's single source of truth. Realizes the
  "skill-ready" architecture goal noted in `docs/architecture.md`.
- **Docs:** New `prompts/` folder containing copy-paste handoff prompts:
  three module-generation prompts (one each for Modules 2, 3, 4) and
  one Moodle upload walkthrough. Each is self-contained so a fresh
  agent with no prior conversation context can execute it.

### Changed
- **AGENTS.md** rewritten for the agent-driven workflow. Points new
  agents at the runbook, spec doc, and journal.
- **docs/architecture.md** updated to describe the three-phase
  pipeline (Python extract → agent authoring → Python finalize) and
  the constraints that drove the design.
- **courses/aviation-weather/course.json** now records each module's
  source-file grouping (per Evgeny's plan) and a generation status
  field.


### Added
- `CHANGELOG.md` (this file) and `docs/journal.md` for ongoing documentation.
- Journal entry recording the three rendering bugs found during the Module 1
  Moodle upload (CSS variables in SVG, relative image paths, full HTML
  document wrappers). These motivate the next several pipeline changes.

### Changed
- **Pipeline:** SVG diagrams now use literal hex colors only — `var(--xxx)`
  references are forbidden inside SVG attributes. Strengthened the lesson
  generation prompt and added a `_inline_css_vars_in_svgs` post-processing
  pass that scrubs any leftover var() references using
  `CSS_VAR_HEX_FALLBACKS`. Fixes invisible/colorless diagrams when lessons
  are pasted into Moodle.
- **Design system:** Every rule in `config/design_system.css` is now scoped
  to a `.ims-lesson` wrapper class, including the CSS custom properties.
  Standalone lesson HTML now emits `<body><div class="ims-lesson">…</div>`.
  Lesson generation prompt forbids `<html>/<head>/<body>/<!DOCTYPE>/<style>`
  in model output so the scoping isn't bypassed.

### Added
- **Pipeline:** Each lesson now produces two HTML files — the existing
  standalone `NN_<slug>.html` plus a new `NN_<slug>_moodle.html` body
  fragment for Moodle upload. The fragment has no document wrappers and
  carries a single inline `<style>` block scoped to `.ims-lesson`. The
  module overview is also dual-emitted as `00_module_overview_moodle.html`.
- **Tooling:** New `pipeline/embed_images.py` script. Walks a module's
  `*_moodle.html` files and rewrites every resolvable `<img src="...">`
  into a base64 `data:` URI so the HTML is self-contained for Moodle.
  Idempotent — safe to re-run after sourcing more images.
- **Tooling:** New `pipeline/retrofit_to_moodle.py` script. Converts a
  module generated by the old pipeline (standalone HTML, unscoped CSS,
  `var(--xxx)` in SVGs) into the new body-fragment format without
  re-running the LLM. Used to bring Module 1 forward without re-generation
  cost.
- **Module 1:** Retrofitted to the new format. Each lesson now has a
  companion `*_moodle.html` body fragment with images embedded as base64
  and SVG colors inlined. Original standalone HTML left unchanged.

### Added
- **Tooling:** New `pipeline/build_combined_page.py`. Concatenates a
  module's overview + per-lesson `*_moodle.html` fragments into a single
  `module_combined_moodle.html` file with a sticky table of contents and
  anchor links. This is the file the user pastes into a single Moodle
  Page activity per module. Replaces the deleted Module-1-specific
  `build_preview.py`.
- **Pipeline:** `embed_images.py` now optimizes images on the fly when
  Pillow is available — downscale to max 1200 px wide, JPEG quality 82.
  Cuts the Module 1 combined page from 12.8 MB to 1.05 MB. Falls back
  to raw bytes when Pillow is missing or the optimizer would produce a
  larger file than the original.
- Added `Pillow` to `requirements.txt`.
- **Tooling:** New `pipeline/extract_sources.py`. Pure-Python extraction
  of PPTX/PDF/DOCX content into a JSON dump. No LLM, no API key
  required. First half of the refactor that removes API-key dependence
  from the pipeline; see journal entry "Pivot to agent-driven pipeline".
- **Tooling:** New `pipeline/finalize_module.py`. Pure-Python "post-LLM"
  step: combines per-lesson quiz XMLs, embeds local images as base64,
  builds the combined Moodle page, regenerates `IMAGES_TO_SOURCE.md`
  from any remaining placeholders, and writes a standard `README.md`
  for the module. Idempotent — safe to re-run after sourcing more
  images or after the agent regenerates a lesson.

### Changed
- **Module 1:** Regenerated all `*_moodle.html` fragments and the new
  `module_combined_moodle.html` with optimized image payloads. The
  original `lessons/Images/*.png` files are left at full resolution.

### Removed
- `pipeline/module_pipeline.py` — the original API-key-dependent
  orchestrator. Its extraction logic now lives in
  `pipeline/extract_sources.py`; its assembly logic now lives in
  `pipeline/finalize_module.py`; its LLM prompts will be reborn in
  `docs/lesson_spec.md`. The agent-driven workflow does not need an
  Anthropic API key.
- `prompts/module_generation.md` — legacy single-shot prompt that
  matched the old script's standalone-HTML output. Superseded by the
  new spec doc + runbook.

### Added
- **Docs:** New `docs/runbook.md` — the step-by-step procedure for
  generating a module end-to-end. Designed to be readable by both
  humans and AI agents; will seed the future Claude skill's quick
  start.
- **Docs:** New `docs/lesson_spec.md` — the contract between the
  Python pipeline tools and whoever (agent or human) authors the
  lessons. Covers audience and tone, the module structure JSON,
  body-fragment HTML shape, design-system classes, SVG color palette,
  quiz XML schema, file naming, the module overview template, and
  common mistakes. This is the file a fresh Claude Code agent reads
  before starting any course generation work.

### Removed
- Pre-Moodle dev scripts that became dead weight after the pivot:
  `pipeline/extract_content.py` (duplicated by `module_pipeline.py`),
  `pipeline/combine_xml.py` (assembly stage handles this),
  `pipeline/replace_images.py` (Module-1-only; superseded by
  `embed_images.py`), and `pipeline/build_preview.py` (Module-1-only;
  to be replaced by the upcoming combined-page generator).
- `courses/aviation-weather/module-1/preview/` — output of the deleted
  `build_preview.py`.
- End-of-pipeline `.zip` packaging step in `module_pipeline.py`. Was for
  bundling output for distribution; obsolete now that Moodle is the
  delivery target.

### Pipeline status
- Module 1 (Aviation Weather Fundamentals & Regulations) — generated and
  manually uploaded to Moodle during the pilot phase. Known issues with
  rendering are being addressed; see journal entry 2026-05-19.
- Modules 2–4 — pending. Source files already in
  `courses/aviation-weather/source_files/`.
