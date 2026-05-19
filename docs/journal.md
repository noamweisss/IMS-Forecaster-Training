# Engineering Journal

This is a chronological log of decisions, dead-ends, and lessons learned while
building the IMS Course Factory pipeline. Newest entries at the top. The
[changelog](../CHANGELOG.md) records *what* changed; this file records *why*.

When this Aviation pilot succeeds, the contents of this journal — especially
the runbook entry — will seed a Claude skill that turns a folder of source
presentations into a Moodle `.mbz` backup automatically.

---

## How to read this file

Each entry has a date, a short headline, and three sections:

- **Context** — what we were trying to do.
- **Decision / Finding** — what we did or learned.
- **Why** — the reasoning, including alternatives considered.

Keep entries small and focused. One topic per entry. When a decision is
later reversed, add a new entry rather than editing the old one.

---

<!-- New entries appended below -->
## 2026-05-20 — Skill-packaging the pipeline: `.claude/skills/generate-module/`

**Context.** AGENTS.md has long promised that an in-repo skills folder would
hold "the course-conversion skill that this repo will seed", and
`docs/architecture.md` mapped the three-phase pipeline directly onto a
skill's anatomy (tools → instructions → worked example). The
agent-driven pivot from 2026-05-19 was made specifically to enable this
packaging. With Module 1 stable and the spec doc settled, this is the
moment.

**Path correction.** The original AGENTS.md placeholder pointed at
`.ai/skills/`, which is not what either tool we use actually reads —
Claude Code looks in `.claude/skills/`, Antigravity looks in
`.agents/skills/`. The placeholder was a guess made before the real
conventions were verified, and the first version of this entry inherited
the wrong path. Lesson worth recording: search for the real convention
(or test it) before deferring to documented intent, especially when the
documentation predates the tools it's trying to describe. The skill now
lives at `.claude/skills/generate-module/` as the canonical home, with
an identical mirror at `.agents/skills/generate-module/`.

**Decision.** Created `.claude/skills/generate-module/`:
.claude/skills/generate-module/
├── SKILL.md                       entry point, ~188 lines
└── references/
├── lesson_template.html       worked-example lesson body fragment
└── quiz_template.xml          worked-example Moodle XML quiz
SKILL.md is the agent's entry point: it describes the three-phase
workflow, points at the right reference files at the right moments,
states the non-negotiable constraints with a one-sentence *why* each,
and ends with five sanity-check commands the agent runs against its
own output. The two reference files are copy-paste scaffolding the
agent uses as a starting point per lesson and quiz.

The skill **does not duplicate** `docs/lesson_spec.md`,
`docs/runbook.md`, or `config/design_system.css`. SKILL.md points at
them by path. This preserves single source of truth and means edits
to the spec or design system flow into the skill automatically.

**Why these specific choices.**

*Bundling vs. linking to repo files.* The skill could have been
self-contained — copying the Python scripts, the spec, the CSS into
the skill folder so it could be lifted into other repos as-is.
Rejected: this skill is only intended for use within this repo, and
duplication creates exactly the sync-drift problem we built the
single-extract / single-finalize architecture to avoid. The trade-off
is that the skill is now repo-coupled; if it ever needs to live
elsewhere the missing pieces are well-scoped and easy to copy in.

*Design system CSS as a marker comment, not embedded text.* The
lesson template carries a loud comment instructing the agent to paste
`config/design_system.css` verbatim into the leading `<style>` block,
rather than embedding the 70 lines of CSS directly. Same
single-source argument. The trade-off is real — an agent could leave
the marker in place by accident — but SKILL.md reinforces the step
twice, and the sanity checks catch the most common downstream
failure (CSS vars in SVG) which would also catch a missing style
block.

*Worked example uses generic meteorology, not aviation.* The lesson
template teaches atmospheric stability. Reasoning: the skill is
course-agnostic and should stay that way; tying the example to
Aviation invites future Hebrew-language or non-aviation courses to
copy aviation patterns inappropriately. The example is still
deliberately rich enough to demonstrate every building block —
callouts (all four classes), table, SVG with literal hex, image-needed
placeholder, summary.

*Two question patterns in the quiz template.* "Diagnose the
classification" and "Forecast-decision from a multi-input scenario"
are the two question shapes that consistently produce
application-level questions in forecasting. Showing both — rather
than one — discourages the model from defaulting to recall.

**What this unlocks.** Future modules (Aviation 2, 3, 4 plus any new
course) can be generated by an agent whose context contains nothing
but the user's request, a pointer to the source files, and this
skill. No prompt engineering per module, no copy-pasted handoff
prompts in `prompts/`.

**Open questions for the next iteration.**

- Will the agent actually paste `design_system.css` into the leading
  `<style>` block correctly, or will the marker comment fail in
  practice? Module 2 generation will tell us.
- The lesson template uses generic meteorology content. Does the
  agent produce better lessons when the example is closer to the
  target domain, or worse — because it's tempted to copy the
  example's content? Empirical question.

The next test is real: generate Aviation Module 2 using this skill in
Antigravity or Claude Code and review the output. Iteration will be
driven by what that review surfaces, not by speculation now.

## 2026-05-19 — Module 2 Generation and PPTX Extraction Fixes

**Context.** Generating "Module 2: In-flight Aviation Hazards" using the new agent-driven workflow. This was the first time the pipeline was used to process a bulk set of source PPTX files in a production capacity.

**Finding.** The PPTX extraction script (`pipeline/extract_sources.py`) failed on several files with `ValueError` when encountering non-placeholder shapes (e.g., logos, custom graphics) or certain chart objects. Specifically, accessing `shape.placeholder_format` on a shape that isn't a placeholder raised an exception, as did checking for a `chart` attribute via `hasattr` on some modern PowerPoint objects.

**Decision.** 
1.  **PPTX Extraction Fix:** Refactored `extract_pptx` to use `getattr(shape, "is_placeholder", False)` and `getattr(shape, "has_chart", False)` for safer attribute access. This allows the script to gracefully skip decorative or complex objects without crashing the entire extraction.
2.  **Module 2 Output:** Successfully generated 5 lessons with quizzes. Adhered to the new Moodle-ready fragment spec (scoped CSS, body fragments, literal SVG hex colors).
3.  **Image Tracking:** Explicitly used `IMAGES_TO_SOURCE.md` to flag two visuals (Annotated Tephigram and Mature CB) that require real photography, while using robust SVG diagrams for all other conceptual illustrations (mountain waves, icing profiles, etc.).

**Why.** 
-   **Robustness:** The pipeline must be resilient to variations in source file formatting. Israel Meteorological Service presentations often contain legacy or inconsistently formatted slides; the extractor needs to be permissive.
-   **Maintenance:** Consolidating the Image Sourcing requirements into a machine-parsable markdown file allows the human SME (Evgeny) to quickly see what is missing without reading every HTML file.

---

## 2026-05-19 — Pilot phase findings: Moodle paste rendering is broken

**Context.** Module 1 was generated by the pipeline during the pilot phase
(before the Moodle server was available) and then manually uploaded once
the Moodle VM came online. The lessons render visibly worse in Moodle than
in the standalone preview HTML: diagrams have no colors, some are missing
entirely, and the sourced photographs fail to load.

**Finding.** Three independent problems in the generated HTML:

1. **CSS custom properties (`var(--xxx)`) used as SVG attribute values.**
   Every inline SVG uses things like `fill="var(--accent)"` and
   `fill="var(--bg)"`. These resolve correctly in the standalone HTML
   because the same file declares the variables in its `<style>` block.
   When the HTML is pasted into Moodle's Page editor, Moodle strips or
   re-scopes that style block, and the SVG references fall back to
   `currentColor` / default — usually black on black or invisible.
2. **Relative image paths.** Lessons reference images as
   `<img src="images/foo.png">`. Moodle does not have a sibling
   `images/` folder; it serves files via `pluginfile.php` using
   `@@PLUGINFILE@@/foo.png` placeholders. The relative paths produce
   broken-image icons.
3. **Full HTML document wrappers.** Each lesson file is a complete
   `<!DOCTYPE html>...<html>...<body>...` document. Moodle's HTML editor
   expects a body fragment; the outer wrappers either get stripped
   silently or break the editor's structure detection.

**Why this matters for the future skill.** Any "convert to Moodle"
pipeline must treat the Moodle HTML editor as a *hostile* host — assume
the `<style>` block will not survive, assume only a body fragment will
render, assume external file references must use Moodle's pluginfile
protocol (or be inlined). These three rules apply to all future courses,
not just Aviation.

**Decision.** Three fixes, one per commit:

- Resolve `var(--xxx)` → literal hex inside every generated SVG attribute.
- Scope the surviving CSS to a `.ims-lesson` wrapper so Moodle's theme
  cannot override our typography and our CSS cannot leak.
- Emit a `*_fragment.html` body-only output alongside the standalone
  page. The standalone is still useful for preview / browser review;
  the fragment is what gets uploaded.

Plus a separate decision (next entry) to embed sourced photos as base64
data URIs inside the HTML — avoiding the `pluginfile.php` problem
entirely.

**Alternatives considered.**

- *Keep standalone HTML, host on a side server, iframe into Moodle.*
  Rejected: requires IT to allow a second internal host. Out of scope.
- *Use Moodle "Book" resource instead of "Page".* Same paste-stripping
  behavior; doesn't help.
- *Rewrite SVGs to use literal colors only.* This is what we're doing.

---

## 2026-05-19 — Belt-and-suspenders SVG color scrubbing

**Context.** The lesson generation prompt now forbids `var(--xxx)` inside
SVG attributes (see previous entry). But we should not rely on the model
following the rule 100% of the time — past output has shown it slips back
into `fill="var(--accent)"` even when the prompt says otherwise.

**Decision.** Add `_inline_css_vars_in_svgs(html)` in
[module_pipeline.py](../pipeline/module_pipeline.py). It walks every
`<svg>...</svg>` block in the model's `html_content` output and substitutes
any `var(--name)` reference with a hex value from the
`CSS_VAR_HEX_FALLBACKS` table. References outside SVGs are left alone — they
live in real CSS rules and resolve normally. Unknown variable names are
left visible (`var(--unknown)`) so the bug is loud rather than silent.

**Why a fallback map and not just a token-by-token color replacement.** The
map is a single source of truth that mirrors
[design_system.css](../config/design_system.css). When we change a token in
the design system, the SVG fallback follows automatically (well — when we
remember to update the map; that's the trade-off).

**Why light-mode values only.** Inline SVGs can't switch colors based on
`prefers-color-scheme` because the SVG attributes are static at render
time. Picking light-mode hex (`#FFFFFF` for `--bg`, `#1A1917` for `--text`)
guarantees readability on most Moodle themes. If we ever need dark-mode
SVGs we'd switch to CSS-driven recoloring via `currentColor` + class-based
overrides — out of scope for the pilot.

---

## 2026-05-19 — Scope lesson CSS to `.ims-lesson`

**Context.** The design system CSS used unscoped selectors (`h1`, `p`,
`.callout`, …). In standalone HTML that's fine — the styles only apply
within the document. But when the body fragment is embedded in a Moodle
Page, Moodle's *own* theme is also styling those elements. Without
scoping we either lose typography (Moodle wins) or pollute Moodle UI
(we win, but we override site nav, etc.).

**Decision.** Move every rule under a `.ims-lesson` class selector. Every
lesson body is wrapped in `<div class="ims-lesson">…</div>`. The
`:root` CSS variables move to `.ims-lesson` too, which means callouts and
tables still resolve their colors but only within our wrapper.

The `_html_page()` helper now emits `<div class="ims-lesson">` inside
`<body>` and adds a tiny `body { margin: 0; background: #fff; }` reset so
the preview still looks right. The lesson generation prompt is also
updated to forbid `<html>`, `<head>`, `<body>`, `<!DOCTYPE>`, and
`<style>` tags in the model's output — preventing the model from undoing
the scoping.

**Trade-off.** The `prefers-color-scheme: dark` media query still flips
the CSS variables, but only inside `.ims-lesson`. Moodle's own dark theme
(if installed) won't recolor the lesson because Moodle uses its own
mechanism, not the OS preference. We accept this — lessons will read
fine on light Moodle themes, and on dark themes the lesson will be a
light island. Better than dim text on the host's dark background.

---

## 2026-05-19 — Two output flavors: standalone + Moodle fragment

**Context.** A single HTML output served both browser-preview and
Moodle-upload duties. That worked accidentally in the pilot only because
both happened to render the styles. With Moodle in the loop properly,
we need two distinct outputs.

**Decision.** Every lesson now produces two files:

- `NN_<slug>.html` — full standalone HTML for browser review. Has
  `<!DOCTYPE>`, `<html>`, etc.
- `NN_<slug>_moodle.html` — body fragment for upload. No document
  wrappers. Contains a single inline `<style>` block at the top
  (scoped to `.ims-lesson`) followed by the `<div class="ims-lesson">`
  wrapper. This is what the `.mbz` builder will consume.

Same dual output for `00_module_overview.html` / `_moodle.html`.

The fragment includes its own scoped `<style>` block. Moodle's HTML
filter for trusted user roles (teacher, manager) preserves inline
`<style>` tags. If KSES strips them on a stricter host, the lesson will
still render — typography falls back to Moodle's theme — but callouts
and tables will lose their colors. We'll learn whether that's an issue
once the Module 1 restore happens.

**Why not inline-style every element instead.** Inline styles would
work even with the harshest KSES filter, but the HTML balloons in size,
loses semantic readability, and makes manual edits painful for Evgeny's
later review pass. A `<style>` block is the right level of abstraction
for the audience.

---

## 2026-05-19 — Sidestep the image-upload problem with base64 data URIs

**Context.** Module 1 referenced four sourced photographs as
`<img src="images/foo.png">`. In Moodle this produced broken-image icons
because Moodle serves files via `pluginfile.php` URL placeholders, not
relative paths.

**Decision.** New script `pipeline/embed_images.py` walks every
`*_moodle.html` in a module folder and rewrites each `<img src="...">`
that resolves to a local file into a base64 `data:image/...;base64,...`
URI. The HTML becomes self-contained — no separate upload step.

The script is idempotent: already-embedded data: URIs are left alone,
external URLs (http/https/protocol-relative) are left alone, unresolved
relative paths are reported but not modified.

**Why a separate script and not inside `module_pipeline.py`.** Image
sourcing is a *human* step in the middle of the pipeline. The model
emits `<div class="image-needed">` placeholders, the human reviews
`IMAGES_TO_SOURCE.md`, fetches appropriate photographs, drops them into
`lessons/Images/`, and only then can embedding happen. Putting embedding
in `module_pipeline.py` would force the pipeline to either rerun
end-to-end after manual sourcing or skip images entirely. A separate
script lets the human run it whenever they have new images.

**Workflow per module.**

1. Run the pipeline → get `*_moodle.html` with `image-needed` placeholders
   and an `IMAGES_TO_SOURCE.md` list.
2. Human sources images, saves to `lessons/Images/<filename>`, and edits
   the matching placeholder div into an `<img src="images/Images/...">`
   tag. (Or `replace_images.py` does this for known names — see
   Module 1 pattern.)
3. Run `python pipeline/embed_images.py --module <dir>` →
   relative `<img>` sources become base64 data URIs in place.
4. Run the `.mbz` builder (next commit set) → ship to Moodle.

**Page size impact.** A 200 KB JPEG embeds to ~270 KB of base64 text.
A module with 4 images grows the HTML by ~1 MB total. Moodle's content
field is `LONGTEXT` (4 GB cap); 1 MB is fine. Loading is actually
*faster* than separate file requests because there's no second round
trip.

**Module 1 footnote.** The sourced PNGs for Module 1 are ~2.5 MB each
at full resolution, producing ~3.3 MB fragments after base64. Still
fine for Moodle, but a future improvement would be to add a small
image-optimization step (resize to max 1200 px wide, JPEG quality 80)
in the embed script. Out of scope for the pilot; flagged for the
runbook.

---

## 2026-05-19 — Module 1 retrofit (no re-run, no LLM cost)

**Context.** Module 1 was generated weeks ago by the older pipeline. Its
lesson HTML uses the obsolete output shape (full document wrapper,
unscoped CSS, `var(--xxx)` in SVG attributes). Re-running the pipeline
would cost API budget and produce slightly different prose due to LLM
non-determinism.

**Decision.** New script `pipeline/retrofit_to_moodle.py` rewrites
existing standalone HTML into the new fragment format without calling
any model. For each lesson it:

1. Extracts the inside of `<body>...</body>`.
2. Strips the pre-existing inline `<style>` block.
3. Runs the SVG var-scrubber from commit 3.
4. Wraps in `<div class="ims-lesson">` and prepends the shared design
   system CSS.
5. Writes `lessons/NN_<slug>_moodle.html` alongside the original.

Then `pipeline/embed_images.py` runs on the output and inlines the four
sourced photographs as base64. Result: zero API calls, content
preserved verbatim, Module 1 ready for the upcoming `.mbz` builder.

**The retrofit script's continuing value.** Anyone reviving an old
module (or a course generated with an even older fork) can reuse it
the same way. Keeping it in the tree.

**Verified after retrofit:**
- All `var(--xxx)` references now live only inside the leading `<style>`
  block. Zero inside `<svg>` elements (sampled with regex).
- All four sourced images are base64-embedded.
- Fragment sizes 3.2–3.5 MB; module overview is 6.5 KB (no images).

---

## 2026-05-19 — Pivot away from .mbz builder; clean up pre-Moodle scripts

**Context.** The original plan included building a `.mbz` (Moodle backup)
generator so the user could upload one file per course. Investigating
the actual schema revealed it's a 1–2 day engineering project — many
XML files, strict cross-reference IDs, version-specific differences, no
forgiveness on errors. With the Moodle version unknown and a same-day
deadline, the risk/reward was bad.

**Decision.** Drop the .mbz path. Replace with a much simpler workflow:

- **One combined HTML page per module** (overview + all lessons stacked,
  with an in-page table of contents). User pastes it as a single Moodle
  Page activity per module. 4 pastes total.
- **Existing quiz XML import.** The pipeline already produces
  `module_quiz_all_questions.xml` per module. User imports it into the
  Question Bank → creates one Quiz activity per module.

Two clicks per module, eight clicks total for the course. Standard
Moodle workflows that IT and Evgeny already know. Re-tryable on any
Moodle version.

**Cleanup that fell out of the pivot.** Several scripts in `pipeline/`
were pre-Moodle dev tools that became dead weight once we adopted the
new fragment-based output:

- `extract_content.py` — earlier standalone extractor. Now duplicated by
  the `extract_*` functions inside `module_pipeline.py`.
- `combine_xml.py` — combined per-lesson quiz XMLs. Replaced by the
  pipeline's assembly stage, which writes `module_quiz_all_questions.xml`
  directly.
- `replace_images.py` — Module-1-only hardcoded image swaps. Superseded
  by `embed_images.py`, which is generic.
- `build_preview.py` — Module-1-only sidebar-navigation preview. Will be
  superseded by the combined-page generator (next commit).
- `module-1/preview/` — output of `build_preview.py`.
- End-of-pipeline `.zip` packaging — was for ZIP-bundle distribution
  back when there was no Moodle to upload to.

All deleted in this cleanup commit. None of them are referenced from
the live pipeline. Anyone digging through `git log` can recover them if
ever needed.

---

## 2026-05-19 — Image optimization on embed: 13 MB → 1 MB combined page

**Context.** First run of `build_combined_page.py` on Module 1 produced
a 12.8 MB HTML file. The four sourced PNGs are ~2.5 MB each at full
resolution (multi-megapixel), but the on-screen render is capped at
840 px wide. Embedding them at native size is pure waste, and pasting
13 MB into a Moodle HTML editor is going to either freeze the browser
or hit PHP's `post_max_size` limit.

**Decision.** Add an optimization step inside `embed_images.py`. When
Pillow is available, every image is downscaled to a max width of
1200 px (1.5× the lesson container width — leaves headroom for retina
displays) and re-encoded as JPEG quality 82. The original PNG files in
`lessons/Images/` are left untouched — only the embedded data URIs are
optimized. This way the standalone HTML preview and any future re-runs
still have the originals.

**Result.** Module 1 combined page: 12.8 MB → 1.05 MB. Per-lesson
fragments: 3.3 MB → 280 KB. Visual quality of the embedded photos is
indistinguishable from the originals at the rendered size.

**Why Pillow specifically.** Already familiar dependency in
data/image-processing Python projects. Added to `requirements.txt`. The
embed script falls back gracefully to raw bytes if Pillow is missing —
the user just gets a bigger but still valid file.

**Fallback rule.** If optimization ever produces a larger output than
the original (small images with a lot of high-frequency detail can
sometimes do this), the script keeps the original bytes. Belt-and-
suspenders against pathological cases.

---

## 2026-05-19 — Pivot to agent-driven pipeline (no API keys)

**Context.** `module_pipeline.py` was built around `anthropic.Anthropic()`
calls — it expected an `ANTHROPIC_API_KEY` env var and billed against
that account. But the user has never operated that way: Module 1 was
generated using Antigravity's bundled Gemini 3.1 Pro inference, and
future modules will be generated by Claude Code agents using the user's
Claude Pro subscription. There's no billed API account in the picture,
and there shouldn't be — IDE-bundled inference is the whole point.

**Decision.** Split the pipeline into Python-only stages and a
documented agent-driven stage:

1. **Python — extract.** `pipeline/extract_sources.py` reads
   PPTX/PDF/DOCX into a JSON dump. No LLM. This used to be Stage 1
   inside `module_pipeline.py`; now it's standalone.
2. **Agent — design + author.** A Claude Code agent reads the JSON
   plus a course config, designs the lesson structure, writes each
   lesson as an HTML body fragment, writes the quiz XML, and writes
   the module overview. The agent operates inside this repo using the
   user's IDE-bundled inference — no API key, no billing.
3. **Python — finalize.** `pipeline/finalize_module.py` (upcoming)
   embeds images, builds the combined Moodle page, and writes the
   per-module README. No LLM.

The current `module_pipeline.py` will be deleted in a follow-up commit
once its remaining logic is preserved in the new files and in the
forthcoming lesson-output spec.

**Why this is also the skill shape.** A Claude skill is essentially:
"here are tools you can run, here's what to produce, here's how the
parts fit." That maps one-to-one onto the new structure:
`extract_sources.py` and `finalize_module.py` become the skill's
exposed tools; the lesson-output spec becomes the skill's
instructions; the runbook becomes the skill's worked example.

Designing the pipeline this way now means lifting it into a skill later
is mostly a copy-paste job.

---

## 2026-05-19 — Retire `module_pipeline.py` and the legacy prompt file

**Context.** With extraction split into `extract_sources.py` and
assembly into `finalize_module.py`, the original `module_pipeline.py`
has nothing left to do that isn't either duplicated or unused. Its
`anthropic.Anthropic()` calls were never the user's actual workflow.

**Decision.** Delete `pipeline/module_pipeline.py` and the legacy
`prompts/module_generation.md` (which referenced the old
`./module_output/` paths and the obsolete standalone-HTML output).

The valuable knowledge these files carried — the BLUEPRINT_SYSTEM /
LESSON_SYSTEM prompts, the quiz XML shape, the SVG color palette and
callout class conventions — will be reconstructed into the new
`docs/lesson_spec.md` (next commit). The spec doc is what a future
Claude Code agent or skill reads to know what to produce.

Both deleted files remain in `git log` if anyone ever needs to
reference the original prompt phrasing.
