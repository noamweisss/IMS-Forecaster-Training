# Restore a `.mbz` into Moodle (the one-upload path)

This is the fastest way to get a course into Moodle: build one `.mbz` backup and
restore it. The whole course comes in with all pages, quizzes, questions, images,
and feedback already wired — no pasting, no question-bank import.

If your Moodle blocks restores or runs an incompatible version, use the
copy-paste fallback in [upload-to-moodle.md](upload-to-moodle.md) instead.

---

## Step 1 — Build the backup

From the repo root:

```bash
# whole course in one file (normal case):
python pipeline/build_mbz.py --course courses/aviation-weather
# -> courses/aviation-weather/aviation-weather.mbz

# or just one module (to re-upload a single updated module):
python pipeline/build_mbz.py --module courses/aviation-weather/module-1
# -> courses/aviation-weather/module-1/aviation-weather-module-1.mbz
```

The build is fast and reads only the finalized `*_moodle.html` + `*_quiz.xml`
files, so it does **not** need the source PowerPoints or Git-LFS. Generated
`.mbz` files are gitignored — rebuild any time.

> Run `python pipeline/finalize_module.py --module <folder>` first if you have
> changed any lesson or quiz since the last finalize. Add `--mbz` to that command
> to finalize and build the module's `.mbz` in one step.

## Step 2 — Restore it in Moodle

1. Open the target course (or create an empty one).
2. **Course menu (gear / "More") → Restore.**
3. Under **Import a backup file**, drag the `.mbz` into the box → **Restore**.
4. **Confirm** (review the backup details) → **Continue**.
5. **Destination:** choose **Merge the backup course into this course** (keeps
   your existing course and adds the content), then **Continue**. (To create a
   brand-new course instead, pick "Restore as a new course".)
6. **Settings** → Continue. **Schema** → here you can rename/untick any section
   or activity; leave as-is for everything → **Continue**.
7. **Review** → **Perform restore** → **Continue** when it finishes.

## Step 3 — Check it

Each module appears as its own section, laid out as:

```
Module overview (Page)
  Lesson 1 (Page)
  Lesson 1 — Quiz
  Lesson 2 (Page)
  Lesson 2 — Quiz
  ...
```

Spot-check:
- A lesson page renders with its diagrams, tables, callouts, and photos
  (images are embedded, so nothing should be a broken-image icon).
- A quiz opens, you can answer, and on submit/review you see the correct answer
  and the rationale (general feedback).

## After restoring

- Set each quiz's **Grade to pass** (e.g. 75%) in the quiz settings if you want a
  pass threshold — the backup leaves it at 0.
- Quizzes are set to "deferred feedback" (answer everything, then submit and
  review). Change the behaviour in the quiz settings if you prefer.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Restore rejected: "backup version" / "not compatible" | Your Moodle is older than 5.2 | The builder targets Moodle 5.2+ (`backup_version 2026042000`). Export a fresh reference backup from your Moodle and tell the agent — or use the copy-paste fallback. |
| Upload fails on a big file | `.mbz` larger than your Moodle upload limit | Build per-module files (`--module`) and restore them one at a time. |
| Images missing | Lesson HTML wasn't finalized (images not embedded) | Re-run `finalize_module.py --module <folder>`, then rebuild the `.mbz`. |
| Quiz has no questions after restore | Restored with "users/anonymise" quirks, or an old Moodle | Confirm Moodle 5.2+; re-build and retry. Report to the agent with the Moodle version. |
