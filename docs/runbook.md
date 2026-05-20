# Course-to-Moodle Runbook

Step-by-step procedure for turning a folder of source presentations into
a Moodle-ready module. Designed to be readable by both humans and AI
agents — a future Claude skill will use this as its instructions.

Read [lesson_spec.md](lesson_spec.md) first if you're authoring lessons.
Read [journal.md](journal.md) if you need to understand *why* any of
this is the way it is.

---

## Prerequisites (one-time per machine)

```bash
pip install -r requirements.txt
```

That installs `python-pptx`, `pymupdf`, `python-docx`, and `Pillow`. No
API key is required at any point — the LLM stage runs inside your IDE.
`anthropic` is also in `requirements.txt` for historical reasons; it
isn't used by any current script.

### Git LFS (required — source files are tracked through LFS)

Every PPTX/PDF/DOCX/PNG in this repo is stored via Git LFS (see
`.gitattributes`). A normal `git clone` will hand you 130-byte pointer
stubs, not the real files. Install LFS and pull the binaries before
running any pipeline command:

```bash
git lfs install
git lfs pull
```

**Claude Code on-the-web (and other proxied sandboxes).** The sandbox's
git remote routes through a local proxy that does not forward the LFS
batch API — `git lfs pull` returns `HTTP 502`. Bypass the proxy by
pointing `lfs.url` at GitHub directly:

```bash
apt-get install -y git-lfs               # not preinstalled in the default image
git lfs install --skip-repo
git config lfs.url https://github.com/<owner>/<repo>.git/info/lfs
git lfs pull
```

This setting lives in `.git/config` and is per-checkout — re-apply it in
every new sandbox session. See `docs/journal.md` (2026-05-20 entry on
the LFS 502) for the full root-cause analysis.

---

## Inputs you need before starting a module

1. **A folder of source files** (PPTX, PDF, DOCX). For the Aviation
   course these live in `courses/aviation-weather/source_files/`. You
   may need to subdivide them by module first — see "Subdivide sources
   per module" below.
2. **A course config** — at minimum, the module title, the module
   number, the course name, and a one-line audience description. For
   Aviation these come from
   [courses/aviation-weather/course.json](../courses/aviation-weather/course.json).
3. **(Optional) A list of pre-known image filenames** if the source
   material references real photographs you've already sourced.

---

## Phase 1 — Subdivide sources per module (one-time per course)

If your `source_files/` folder contains every module's sources mixed
together, create one subfolder per module first:

```bash
mkdir -p courses/<course>/source_files/module-2
# Then move the right files in:
mv "courses/<course>/source_files/05. Turbulence.pptx" \
   courses/<course>/source_files/module-2/
# ... etc
```

For the Aviation course, the groupings are fixed by Evgeny:

| Module | Source files | Theme |
|--------|--------------|-------|
| 1 | 01–04 | Fundamentals & Regulations |
| 2 | 05–12 | In-flight Aviation Hazards |
| 3 | 13–14 | Terminal Area Hazards & Visibility |
| 4 | 15–18 | Aviation Forecast Products & Warnings |

---

## Phase 2 — Extract source content (Python, no LLM)

```bash
python pipeline/extract_sources.py \
    --input  courses/<course>/source_files/module-N \
    --output courses/<course>/module-N/_extraction.json
```

This reads every PPTX/PDF/DOCX and writes a JSON dump containing slide
titles, body bullets, speaker notes, page text, section headings. The
agent uses this JSON instead of reading the binary files directly.

---

## Phase 3 — Agent designs and authors the module

Open a Claude Code (or equivalent) session in this repo. Hand the agent
these three things:

1. `courses/<course>/module-N/_extraction.json` — the extracted content.
2. `docs/lesson_spec.md` — what to produce.
3. The module's context: title, number, audience, and any specific
   instructions from the course owner.

A sample opening prompt:

> Generate Module N of the Aviation Weather Forecasting Certification
> course. The extracted source content is at
> `courses/aviation-weather/module-N/_extraction.json`. The audience is
> professional meteorologists at IMS seeking aviation forecaster
> certification.
>
> Read [docs/lesson_spec.md](docs/lesson_spec.md) for the exact output
> shape. Produce:
>
>  - `courses/aviation-weather/module-N/module_structure.json`
>  - `courses/aviation-weather/module-N/00_module_overview_moodle.html`
>  - `courses/aviation-weather/module-N/lessons/NN_<slug>_moodle.html`
>    (one per lesson)
>  - `courses/aviation-weather/module-N/lessons/NN_<slug>_quiz.xml`
>    (one per lesson)
>
> Design 3–6 lessons. Each lesson is a self-contained ~20 min unit.
> The module quiz combines 4–8 questions per lesson.

The agent will:

1. Read the extraction JSON.
2. Design a `module_structure.json` (the blueprint).
3. Write each lesson as a body-fragment HTML file (see lesson_spec).
4. Write each lesson's quiz XML.
5. Write the module overview body fragment.

The agent uses the user's IDE-bundled inference — no API key needed.

---

## Phase 4 — Human image sourcing (only if needed)

If the agent flagged any visuals via `image-needed` placeholders, the
sourced images go in `courses/<course>/module-N/lessons/Images/`. Use
the exact filename the agent suggested (or any filename — you'll edit
the placeholder div into an `<img>` tag with the matching `src`).

For each image the agent flagged:

1. Find / take / generate the image.
2. Save it as `lessons/Images/<filename>.png` (or `.jpg`).
3. Open the lesson's `*_moodle.html`, find the corresponding
   `<div class="image-needed" ...>` block, and replace it with:
   ```html
   <figure>
     <img src="images/<filename>.png" alt="...">
   </figure>
   ```

This step is skipped entirely if the agent didn't flag any images.

---

## Phase 5 — Finalize (Python, no LLM)

```bash
python pipeline/finalize_module.py --module courses/<course>/module-N
```

This:
- Combines per-lesson quiz XMLs into `module_quiz_all_questions.xml`.
- Embeds local images as base64 data URIs (downscaled + JPEG-recompressed).
- Builds `module_combined_moodle.html` — the single-paste file.
- Writes `IMAGES_TO_SOURCE.md` if any placeholders remain unfilled.
- Writes the module's `README.md` with upload instructions.

Idempotent. Re-run any time you source more images or the agent
regenerates a lesson.

---

## Phase 6 — Upload to Moodle (manual, 2 clicks per module)

Open the module's freshly-written `README.md` and follow it. The short
version:

1. Create a Moodle Page activity; paste `module_combined_moodle.html`
   into the HTML editor.
2. Question Bank → Import → upload `module_quiz_all_questions.xml`;
   create a Quiz activity drawing from that bank.

Five minutes per module if your hands are warm.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Combined-page paste hangs or errors | File > Moodle `post_max_size` | Use the per-lesson `*_moodle.html` fragments instead — one Page per lesson. |
| Diagrams render without colors | Moodle stripped the `<style>` block | Make sure your user role has trusted-content enabled (Site admin → Security → HTML settings). |
| Images broken after paste | Wrong file pasted | Paste `module_combined_moodle.html`, not `module_combined.html` (no such file) or the standalone lessons. |
| Quiz import fails | Malformed XML | Open `module_quiz_all_questions.xml`, look for unbalanced CDATA or missing `<answer>` blocks. Most often caused by the agent emitting HTML that wasn't CDATA-wrapped. |
| `finalize_module.py` errors with "no lesson fragments found" | Agent didn't write to the expected path | Check the `lessons/` subfolder. Files must end in `_moodle.html`. |
| `extract_sources.py` reports "0 slides" / writes a tiny JSON | Source files are LFS pointer stubs, not real binaries | Run `git lfs pull`. In Claude Code's sandbox, first set `git config lfs.url https://github.com/<owner>/<repo>.git/info/lfs` to bypass the proxy (HTTP 502). See `docs/journal.md` 2026-05-20. |

---

## Adapting for a new course

The pipeline is course-agnostic. For a new course:

1. Create `courses/<new-course>/source_files/` and dump the
   presentations there.
2. Create `courses/<new-course>/course.json` (copy the Aviation file
   and edit).
3. Decide module groupings with the subject-matter expert.
4. Follow phases 1–6 above for each module.

Anything specific to Aviation (the breadcrumb wording, the certification
phrasing) is content the agent writes, not pipeline logic. The agent
takes its cue from the course/module context in your opening prompt.

---

## Future skill packaging

When this workflow is wrapped into a Claude skill, the skill's structure
maps onto this runbook directly:

- `extract_sources.py` and `finalize_module.py` become **tools** the
  skill exposes.
- `lesson_spec.md` becomes the skill's **instructions**.
- This runbook becomes the skill's **worked example** / quick start.

Until then, the procedure above is the manual equivalent.
