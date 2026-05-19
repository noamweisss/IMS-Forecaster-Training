# Upload walkthrough — All 4 modules into Moodle

Use this as a personal checklist, or paste it into an agent that has
browser access to your Moodle instance. Either way, the steps are the
same.

Total time estimate: ~30 minutes (2 minutes per module × 4 modules,
plus ~15 minutes of one-time course setup if you haven't already done
that for the new structure).

---

## Pre-flight checklist

Before touching Moodle, verify in your repo that all four modules have a `module_combined_moodle.html` file and a `module_quiz_all_questions.xml` file:

```
ls -la courses/aviation-weather/module-{1,2,3,4}/module_combined_moodle.html
ls -la courses/aviation-weather/module-{1,2,3,4}/module_quiz_all_questions.xml
```

Each `module_combined_moodle.html` should be in the range **500 KB – 5 MB**. If anything is over 10 MB, the paste may struggle in Moodle's editor — see Troubleshooting at the end.

If any module is missing files, run its `finalize_module.py` step:

```
python pipeline/finalize_module.py --module courses/aviation-weather/module-N
```

## Step 0 — Course setup in Moodle (skip if already done)

If you have a course shell already (the one Module 1 was pilot-uploaded to), you can keep using it. **However**, the pilot upload of Module 1 used the *old* broken format. You'll want to delete those existing Module 1 Pages and re-upload the new combined page. Open the existing Module 1 section, delete the broken Page activity (and any image files you uploaded separately), then proceed to Step 1 below.

If you're starting fresh:

1. Log into Moodle as a teacher/manager.
2. **Site administration → Courses → Add a new course**.
3. Set the course full name and short name. For consistency with the repo, use the title from `courses/aviation-weather/course.json`: **Aviation Weather Forecasting Certification**.
4. **Course format**: Topics format.
5. **Number of sections**: 4 (one per module).
6. Save and view the new course.
7. **Turn editing on**.
8. Rename the four sections in order to the module titles from `course.json`:
   - Section 1: *Module 1: Aviation Weather Fundamentals & Regulations*
   - Section 2: *Module 2: In-flight Aviation Hazards*
   - Section 3: *Module 3: Terminal Area Hazards & Visibility*
   - Section 4: *Module 4: Aviation Forecast Products & Warnings*

## Step 1 — Upload Module N (repeat for N = 1, 2, 3, 4)

Two activities per module: one Page (lesson content), one Quiz (assessment).

### 1A — The lesson Page (~1 minute)

1. In the Module N section: **Add an activity or resource → Page**.
2. **Name**: `Module N: <module title>`. The title is in `courses/aviation-weather/module-N/module_structure.json` under `module_title`.
3. **Description**: leave blank or copy the `module_description` from `module_structure.json`.
4. Click into the **Content** field and find the toolbar's HTML source button. In Atto it's the `</>` icon (you may need to click "Show more buttons" — the down-arrow on the right of the toolbar — to reveal it). In TinyMCE it's labeled **Source code**. Click it to switch to plain HTML mode.
5. Open `courses/aviation-weather/module-N/module_combined_moodle.html` in a text editor. **Ctrl+A → Ctrl+C** to copy the whole file.
6. Paste into Moodle's HTML view (Ctrl+V). The paste may take 2–10 seconds for a 1 MB file — that's normal.
7. Click the source-code button again to return to the visual editor. You should see the module overview at the top, then the table of contents, then each lesson with its diagrams and tables visible. If diagrams are colorless or the layout looks plain, see Troubleshooting.
8. **Save and return to course**.

### 1B — The quiz (~1 minute)

The quiz is two parts — importing questions into the Question Bank, then creating the Quiz activity that uses them.

#### Import questions

1. From the course homepage, click the **gear icon** (top right) → **More**.
2. In the **Course administration** tab, find **Question bank → Import**.
3. **File format**: select **Moodle XML format**.
4. **Import category**: under **General**, click the dropdown and choose **Create new category**. Name it `Module N Questions`.
5. Drag `courses/aviation-weather/module-N/module_quiz_all_questions.xml` into the upload box (or click and select).
6. Click **Import** at the bottom. Moodle will show a preview of every imported question. Scroll to confirm they look right, then click **Continue**.

#### Create the Quiz activity

1. Back at the course homepage, in the Module N section: **Add an activity or resource → Quiz**.
2. **Name**: `Module N Certification Quiz`.
3. **Grade → Grade to pass**: enter `75%` of the maximum grade. If the maximum grade defaults to 10, set the pass mark to 7.50. If you change the max grade later, remember to update this.
4. (Other settings can stay default for now. You can come back later to add things like attempt limits or time limits.)
5. **Save and display** to land on the new quiz's page.
6. Click **Edit quiz**.
7. Click **Add → from question bank**.
8. In the category dropdown, pick `Module N Questions`.
9. Tick the "select all" checkbox at the top, then click **Add selected questions to the quiz**.
10. Optionally tick **Shuffle** at the top of the question list so each student gets a different order.
11. Set **Maximum grade** at the top to `10` (or whatever scale matches your course).
12. Click **Save**.

That's Module N done.

## Step 2 — Final smoke test

After all four modules are uploaded:

1. Open the course as a **student** view (use Moodle's "Switch role to → Student" feature in the gear menu).
2. Open Module 1's Page. Click each entry in the table of contents — confirm it scrolls to the right lesson.
3. Verify at least one diagram renders with color.
4. Verify at least one embedded image renders (Module 1 has four — WMO/ICAO assembly, dispatcher console, airspace wedding cake, Kollsman altimeter).
5. Open Module 1's Quiz. Start an attempt. Answer the first question. Confirm the "Rationale" feedback appears after submitting.
6. Repeat steps 2–5 for each remaining module.
7. **Switch role back** to teacher.

If everything renders cleanly, the upload is complete. Ping Evgeny for content review.

---

## Troubleshooting

### "The paste froze my browser" / "the page didn't save"

Your Moodle's PHP `post_max_size` is smaller than the combined HTML file. Two options:

- **Option A: use per-lesson fragments.** Open the module folder. Instead of one big paste, create one Moodle Page per lesson using `lessons/NN_<slug>_moodle.html`, plus a Page for `00_module_overview_moodle.html`. More clicks (5–6 pastes per module) but each paste is small.
- **Option B: ask IT to raise `post_max_size`.** Bitnami's default is 80 MB which should comfortably fit anything we generate, but custom installs may be lower. Set it to 16 MB minimum.

### Diagrams render in grayscale or have no fills

Moodle is stripping the `<style>` block from your pasted HTML. This happens when your user role doesn't have permission to post "trusted" content. Fix:

1. **Site administration → Users → Permissions → Define roles**.
2. Edit your role (Manager or Teacher).
3. Find the capability `moodle/site:trustcontent` and set it to **Allow**.
4. Then return to your Module N Page activity and re-save. Moodle may need you to re-paste the HTML if the `<style>` block has already been stripped from the database — start over from Step 1A for that module.

Alternative if you can't change permissions: install the "HTML" filter setting at **Site administration → Plugins → Filters → Manage filters** → set **HTML tidy** or any "Multilanguage / Markdown" filter to **Off** for the affected pages.

### Images come out as broken icons

You pasted the wrong file. The combined page (`module_combined_moodle.html`) and per-lesson fragments (`*_moodle.html`) have base64-embedded images and should never produce broken icons. Standalone files (`lessons/NN_<slug>.html` without the `_moodle` suffix) reference `images/foo.png` paths that won't resolve in Moodle. Re-check which file you copied.

### Quiz import shows "0 questions imported"

The XML is malformed. Open `module_quiz_all_questions.xml` and check:

- The file starts with `<?xml version="1.0" encoding="UTF-8"?>` and `<quiz>` and ends with `</quiz>`.
- Each `<question type="multichoice">` has a `<name>`, `<questiontext>`, `<generalfeedback>`, `<defaultgrade>`, `<single>`, `<shuffleanswers>`, and exactly four `<answer>` blocks.

If the file looks corrupted, re-run `python pipeline/finalize_module.py --module courses/aviation-weather/module-N` to regenerate it.

### Quiz import works but every question shows "missing answer text" or HTML markup in the question

Moodle expects HTML inside `<text>` elements to be CDATA-wrapped (`<![CDATA[...]]>`) or entity-escaped. The pipeline's combiner re-serializes XML via Python's ElementTree, which converts CDATA to entity-escaping. Both are valid for Moodle — but if your Moodle version is misbehaving with one of them, edit `pipeline/finalize_module.py`'s `combine_quiz_xmls` function and switch back to manual string concatenation that preserves CDATA. (Last resort. Try the default first.)

### A module's `module_combined_moodle.html` is bigger than 5 MB

The agent that generated it probably used non-base64 image references that got embedded as full-size files, or you have unusually large source images in `lessons/Images/`. Check:

```
ls -la courses/aviation-weather/module-N/lessons/Images/
```

If any image is > 1 MB, downscale it manually before re-running `finalize_module.py`. The pipeline's embedder will optimize during embed, but if a `lessons/Images/foo.png` is 10 MB to start with, the optimization may still leave it at ~500 KB.
