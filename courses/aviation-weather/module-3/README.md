# Aviation Warnings: SIGMET, AIRMET & Aerodrome — Moodle Upload Instructions

## Fastest path — restore a `.mbz` (one upload)

If you have built the backup (`python pipeline/build_mbz.py --course <course-dir>`
for the whole course, or `--module <this-folder>` for just this module), upload
that single `.mbz` instead of pasting anything:

1. In Moodle: **Course → Restore**.
2. Drag the `.mbz` into the upload box → **Restore**.
3. **Merge into this course** (or restore as a new course) → confirm → **Continue**.

The module(s) appear as their own section(s) — overview Page → lesson Page → Quiz
→ … — with all questions, images, and feedback already wired. No question-bank
import needed.

The manual copy-paste workflow below still works as a fallback for hosts that
block restores.

---

## Fallback — copy-paste (two clicks per module)

No image upload, no per-lesson pasting.

## Files in this folder

| File | What it is |
|------|------------|
| `*-module-3.mbz` | **Restore this in Moodle for the one-upload path** (only present if you ran `build_mbz.py --module`). A Moodle backup of this module — overview Page → lesson Page → Quiz per lesson, fully wired. |
| `module_combined_moodle.html` | **Paste this into one Moodle Page activity.** All lessons + overview + table of contents in one self-contained HTML file (images base64-embedded). |
| `module_quiz_all_questions.xml` | **Import this into the Question Bank.** Moodle XML format; every quiz question for the module. |
| `00_module_overview_moodle.html` and `lessons/*_moodle.html` | Per-lesson body fragments. Use these instead of the combined page if your Moodle's `post_max_size` is small. |
| `00_module_overview.html` and `lessons/*.html` | Optional standalone preview HTML for browser review (only present if the agent wrote them). |
| `_extraction.json` / `module_structure.json` | Pipeline artifacts kept for re-runs and debugging. |
| `IMAGES_TO_SOURCE.md` | (Only present if needed.) Visuals the agent flagged for human sourcing. |

## Step 1 — Create the lesson Page (~1 minute)

1. In Moodle, **Turn editing on** in the target course.
2. In the module's section: **Add an activity or resource → Page**.
3. Name it `Aviation Warnings: SIGMET, AIRMET & Aerodrome`.
4. In the **Content** field, click the toolbar's HTML source button (`</>` or "Show more buttons → HTML"). This switches the editor to plain HTML mode.
5. Open `module_combined_moodle.html` in a text editor, **Ctrl+A → Ctrl+C**, paste into Moodle's HTML view.
6. **Save and return to course**.

The page contains a table of contents at the top — students can click any lesson to jump to it.

## Step 2 — Import the quizzes (~1 minute)

1. From the course, open **gear icon → More → Question bank → Import**.
2. **File format:** Moodle XML format.
3. **Import category:** create or pick `Aviation Warnings: SIGMET, AIRMET & Aerodrome Questions`.
4. Drag `module_quiz_all_questions.xml` into the upload box → **Import** → **Continue**.
5. Add a **Quiz** activity to the module's section, name it `Aviation Warnings: SIGMET, AIRMET & Aerodrome Certification Quiz`, and under **Edit quiz → Add → from question bank**, select all the imported questions.
6. Set the **Grade to pass** to 75% in the quiz settings.

## Troubleshooting

- **Combined page paste hangs.** Your Moodle's `post_max_size` may be lower than the file. Fallback: use the per-lesson `*_moodle.html` files — one Page activity per lesson.
- **Diagrams render without colors.** Moodle may be stripping the `<style>` block. Check your user role has trusted-content / extended HTML enabled.
- **Images broken.** Should not happen — images are base64-embedded. If it does, the wrong file was pasted (probably `lessons/01_*.html` instead of `lessons/01_*_moodle.html`).
