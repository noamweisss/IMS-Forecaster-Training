# Hebrew Translation Skills

A pair of Antigravity skills that translate finalized English IMS course
content into Hebrew. Designed to run as two model-specific agents inside
Antigravity's Manager view.

| Skill | Path | Model | Role |
|-------|------|-------|------|
| `translator` | [`translator/SKILL.md`](translator/SKILL.md) | Claude (Opus/Sonnet 4.x — strongest your Antigravity instance offers) | Layer 1. Reads English `module-N/`; writes Hebrew `module-N-he/` with RTL adjustments; emits `_translation_manifest.json`. |
| `editor` | [`editor/SKILL.md`](editor/SKILL.md) | Gemini 3 Pro | Layer 2. Reads both trees + manifest; emits `review.json`. Review-only — never modifies Hebrew files. |

## How they fit together

```
English module-N/
        │
        ▼
[ translator (Claude) ]       ← Layer 1, Antigravity Agent A
        │  Hebrew module-N-he/ + _translation_manifest.json
        ▼
[ pipeline/validate_translation.py ]   ← Optional deterministic preflight
        │  augments review.json with structural findings
        ▼
[ editor (Gemini) ]            ← Layer 2, Antigravity Agent B
        │  review.json (errors, warnings, info)
        ▼
human reviews; re-run translator on flagged issues if needed
        │
        ▼
python pipeline/finalize_module.py --module courses/.../module-N-he
        │  module_combined_moodle.html + README.md (regenerated)
        ▼
Moodle upload (2 clicks)
```

## Shared sources of truth

Both skills read these before doing any work:
- [`docs/hebrew_translation_spec.md`](../../../docs/hebrew_translation_spec.md) — the contract (file shapes, scope, schemas).
- [`docs/hebrew_glossary.md`](../../../docs/hebrew_glossary.md) — bilingual terminology.
- [`docs/lesson_spec.md`](../../../docs/lesson_spec.md) — the English output contract these translations must preserve.

## Running the pipeline

See [`prompts/translate-to-hebrew.md`](../../../prompts/translate-to-hebrew.md)
for a copy-paste handoff prompt that bootstraps a fresh Antigravity
session and walks through the two-agent flow.

## Why two skills, not one

Splitting translation and review into separate agents gives:
- **Independent model choice.** Claude tends to be stronger at long-form
  multilingual translation; Gemini is the native model in Antigravity
  and has tight integration with Google's grounding tools.
- **A clean audit trail.** The translator's `_translation_manifest.json`
  declares what it did; the editor's `review.json` independently
  validates it. No single agent gets to grade its own work.
- **Easy distribution later.** Each `SKILL.md` is self-contained and
  copy-pastable into the global skills directory
  (`~/.gemini/antigravity/skills/`) with no body changes.

## Status

v0.1 scaffolding. Spec, glossary, and skill files are written; first
real translation run (Module 1 → Module 1-he) is pending.
