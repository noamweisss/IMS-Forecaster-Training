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

### Pipeline status
- Module 1 (Aviation Weather Fundamentals & Regulations) — generated and
  manually uploaded to Moodle during the pilot phase. Known issues with
  rendering are being addressed; see journal entry 2026-05-19.
- Modules 2–4 — pending. Source files already in
  `courses/aviation-weather/source_files/`.
