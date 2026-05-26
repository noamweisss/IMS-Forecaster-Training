# Hebrew Translation Skills

A pair of skills that translate finalized English IMS course content
into Hebrew. Designed to run as two agents inside Antigravity's Manager
view, or sequentially in Claude Code or any single-agent IDE.

| Skill | Path | Role |
|-------|------|------|
| `translator` | [`translator/SKILL.md`](translator/SKILL.md) | Layer 1. Reads English `module-N/`; writes Hebrew `module-N-he/` with RTL adjustments; emits `_translation_manifest.json`. |
| `editor` | [`editor/SKILL.md`](editor/SKILL.md) | Layer 2. Reads both trees + manifest; emits `review.json`. Review-only — never modifies Hebrew files. |

## How they fit together

```
English module-N/
        │
        ▼
[ translator ]                ← Layer 1, Antigravity Agent A
        │  Hebrew module-N-he/ + _translation_manifest.json
        ▼
[ pipeline/validate_translation.py ]   ← Optional deterministic preflight
        │  augments review.json with structural findings
        ▼
[ editor ]                    ← Layer 2, Antigravity Agent B
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
- **An independent reviewer.** The two agents run with separate context
  and instructions, so the editor can't inherit the translator's blind
  spots or biases.
- **A clean audit trail.** The translator's `_translation_manifest.json`
  declares what it did; the editor's `review.json` independently
  validates it. No single agent gets to grade its own work.
- **Easy distribution later.** Each `SKILL.md` is self-contained and
  copy-pastable into the global skills directory
  (`~/.gemini/antigravity/skills/`) with no body changes.

## Status

v0.1 scaffolding. Spec, glossary, and skill files are written; first
real translation run (Module 1 → Module 1-he) is pending.
