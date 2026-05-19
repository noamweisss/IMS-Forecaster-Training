# Module 1 — Moodle Upload Instructions

Two clicks. Five minutes. No image upload, no per-lesson pasting.

## Files in this folder

| File | What it is |
|------|------------|
| `module_combined_moodle.html` | **Paste this into one Moodle Page activity.** All lessons + overview + table of contents in a single self-contained HTML file (~1 MB, images base64-embedded). |
| `module_quiz_all_questions.xml` | **Import this into the Question Bank.** Moodle XML format; contains every quiz question for the module. |
| `00_module_overview.html` and `lessons/*.html` | Standalone preview HTML for browser review. Not used for upload. |
| `00_module_overview_moodle.html` and `lessons/*_moodle.html` | Per-lesson body fragments. Fallback path if the combined page is too large for your Moodle instance. |
| `module_structure.json` / `_extraction.json` | Pipeline by-products kept for re-runs and debugging. |
| `IMAGES_TO_SOURCE.md` | List of photographs the AI flagged as needing human sourcing (already done for Module 1). |

## Step 1 — Create the lesson Page (~1 minute)

1. In Moodle, **Turn editing on** in the target course.
2. In the Module 1 section: **Add an activity or resource → Page**.
3. Name it `Module 1: Aviation Weather Fundamentals & Regulations`.
4. In the **Content** field, click the toolbar's HTML source button (`</>` or "Show more buttons → HTML"). This switches the editor to plain HTML mode.
5. Open `module_combined_moodle.html` in a text editor, **Ctrl+A → Ctrl+C** to copy the whole file, then paste into Moodle's HTML view.
6. **Save and return to course**.

The page contains a table of contents at the top — students can click any lesson to jump to it.

## Step 2 — Import the quizzes (~1 minute)

1. From the course, open the **gear icon → More → Question bank → Import**.
2. **File format:** Moodle XML format.
3. **Import category:** create or pick `Module 1 Questions`.
4. Drag `module_quiz_all_questions.xml` into the upload box → **Import** → **Continue**.
5. Add a **Quiz** activity to the Module 1 section, name it `Module 1 Certification Quiz`, and under **Edit quiz → Add → from question bank**, select all the imported questions.
6. Set the **Grade to pass** to 75% in the quiz settings.

That's it. The module is live.

## Troubleshooting

- **Combined page paste hangs or errors out.** Your Moodle's `post_max_size` may be lower than ~2 MB. Fallback: use the per-lesson `*_moodle.html` files — one Page activity per lesson, five pastes instead of one.
- **Diagrams render without colors.** Means Moodle is stripping the `<style>` block from the pasted HTML. Check your user role has trusted-content / "Allow extended characters in HTML" enabled (admin → Site administration → Security → HTML settings).
- **Images broken after paste.** Should not happen — images are base64-embedded. If it does, you pasted the wrong file (probably `lessons/01_*.html` instead of `lessons/01_*_moodle.html`, or the standalone `00_module_overview.html` instead of `module_combined_moodle.html`).
