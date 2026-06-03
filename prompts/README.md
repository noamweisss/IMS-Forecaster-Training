# Handoff Prompts

Copy-paste prompts for handing module generation and Moodle upload to a
fresh agent (or doing the upload yourself with the checklist).

Each file in this folder is one self-contained prompt. Use them in order:

1. [restore-mbz-to-moodle.md](restore-mbz-to-moodle.md) — Build one `.mbz` and restore the whole course in a single upload (recommended)
2. [upload-to-moodle.md](upload-to-moodle.md) — Copy-paste fallback for getting all 4 modules into Moodle by hand

These prompts are agent-agnostic — they work for Claude Code, Antigravity
(Gemini), or any other IDE-bundled agent that can read repo files, write
files, and run Python scripts.
