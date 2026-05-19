# Changelog

All notable changes to the IMS Forecaster Training System pipeline are documented
here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Dates are in YYYY-MM-DD.

The companion [engineering journal](docs/journal.md) records the *why* behind
each change — decisions, dead-ends, lessons learned. New developers (and the
future course-to-mbz Claude skill) should read both.

## [Unreleased]

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

### Pipeline status
- Module 1 (Aviation Weather Fundamentals & Regulations) — generated and
  manually uploaded to Moodle during the pilot phase. Known issues with
  rendering are being addressed; see journal entry 2026-05-19.
- Modules 2–4 — pending. Source files already in
  `courses/aviation-weather/source_files/`.
