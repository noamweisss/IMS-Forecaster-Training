#!/usr/bin/env python3
"""
finalize_module.py — Turn agent-written lesson HTML and quiz XML into a
Moodle-ready module folder.

Pure Python. No LLM. No API key. This is the last step in the new pipeline:

    1. extract_sources.py        -> _extraction.json  (Python-only)
    2. <agent>                   -> writes lesson/quiz/overview files
    3. finalize_module.py        -> Moodle-ready outputs  (this script)

What this script does, given a module folder where the agent has already
written `lessons/NN_<slug>_moodle.html`, `00_module_overview_moodle.html`,
and `lessons/NN_<slug>_quiz.xml`:

    - Combines all per-lesson quiz XMLs into module_quiz_all_questions.xml.
    - Embeds any <img src="..."> that points to a local file in
      lessons/Images/ (or lessons/images/) as a base64 data URI.
    - Builds module_combined_moodle.html (one-paste-into-Moodle file).
    - Writes IMAGES_TO_SOURCE.md from any leftover `image-needed` placeholders.
    - Writes README.md with the standard 2-click upload instructions.

The script is idempotent: re-running picks up any new images that were
sourced since the last run and refreshes the combined page.

Usage:
    python pipeline/finalize_module.py --module courses/aviation-weather/module-2
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from embed_images        import run as embed_run        # noqa: E402
from build_combined_page import build_combined          # noqa: E402


IMAGE_NEEDED_RE = re.compile(
    r'<div\s+class="image-needed"[^>]*data-description="([^"]*)"',
    re.IGNORECASE,
)


def combine_quiz_xmls(module_dir: Path) -> Path | None:
    """Merge every lessons/*_quiz.xml into module_quiz_all_questions.xml.
    Returns the output path, or None if there were no quiz files."""
    lessons_dir = module_dir / "lessons"
    quiz_files  = sorted(lessons_dir.glob("*_quiz.xml"))
    if not quiz_files:
        return None

    root = ET.Element("quiz")
    seen_category = False
    for qf in quiz_files:
        tree = ET.parse(qf)
        for q in tree.getroot().findall("question"):
            # Keep at most one category declaration so Moodle doesn't fight us
            # about duplicate top-level categories at import time.
            if q.get("type") == "category":
                if seen_category:
                    continue
                seen_category = True
            root.append(q)

    out = module_dir / "module_quiz_all_questions.xml"
    ET.ElementTree(root).write(out, encoding="utf-8", xml_declaration=True)
    return out


def collect_image_requests(module_dir: Path) -> list[str]:
    """Read every *_moodle.html in the module and pull out the
    `image-needed` placeholders that still have no sourced image."""
    items: list[str] = []
    for f in sorted((module_dir / "lessons").glob("*_moodle.html")):
        text = f.read_text(encoding="utf-8")
        for desc in IMAGE_NEEDED_RE.findall(text):
            items.append(f"{f.name}: {desc}")
    overview = module_dir / "00_module_overview_moodle.html"
    if overview.is_file():
        for desc in IMAGE_NEEDED_RE.findall(overview.read_text(encoding="utf-8")):
            items.append(f"{overview.name}: {desc}")
    return items


def write_images_to_source(module_dir: Path, items: list[str]) -> Path | None:
    if not items:
        return None
    out = module_dir / "IMAGES_TO_SOURCE.md"
    lines = [
        "# Images To Source",
        "",
        "The lesson generator flagged these visuals as needing a real",
        "photograph or external graphic. Place files into "
        "`lessons/Images/` then re-run `pipeline/finalize_module.py` to",
        "embed them.",
        "",
    ]
    lines.extend(f"- {item}" for item in items)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


README_TEMPLATE = """\
# {module_title} — Moodle Upload Instructions

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
| `*-{module_folder}.mbz` | **Restore this in Moodle for the one-upload path** (only present if you ran `build_mbz.py --module`). A Moodle backup of this module — overview Page → lesson Page → Quiz per lesson, fully wired. |
| `module_combined_moodle.html` | **Paste this into one Moodle Page activity.** All lessons + overview + table of contents in one self-contained HTML file (images base64-embedded). |
| `module_quiz_all_questions.xml` | **Import this into the Question Bank.** Moodle XML format; every quiz question for the module. |
| `00_module_overview_moodle.html` and `lessons/*_moodle.html` | Per-lesson body fragments. Use these instead of the combined page if your Moodle's `post_max_size` is small. |
| `00_module_overview.html` and `lessons/*.html` | Optional standalone preview HTML for browser review (only present if the agent wrote them). |
| `_extraction.json` / `module_structure.json` | Pipeline artifacts kept for re-runs and debugging. |
| `IMAGES_TO_SOURCE.md` | (Only present if needed.) Visuals the agent flagged for human sourcing. |

## Step 1 — Create the lesson Page (~1 minute)

1. In Moodle, **Turn editing on** in the target course.
2. In the module's section: **Add an activity or resource → Page**.
3. Name it `{module_title}`.
4. In the **Content** field, click the toolbar's HTML source button (`</>` or "Show more buttons → HTML"). This switches the editor to plain HTML mode.
5. Open `module_combined_moodle.html` in a text editor, **Ctrl+A → Ctrl+C**, paste into Moodle's HTML view.
6. **Save and return to course**.

The page contains a table of contents at the top — students can click any lesson to jump to it.

## Step 2 — Import the quizzes (~1 minute)

1. From the course, open **gear icon → More → Question bank → Import**.
2. **File format:** Moodle XML format.
3. **Import category:** create or pick `{module_title} Questions`.
4. Drag `module_quiz_all_questions.xml` into the upload box → **Import** → **Continue**.
5. Add a **Quiz** activity to the module's section, name it `{module_title} Certification Quiz`, and under **Edit quiz → Add → from question bank**, select all the imported questions.
6. Set the **Grade to pass** to 75% in the quiz settings.

## Troubleshooting

- **Combined page paste hangs.** Your Moodle's `post_max_size` may be lower than the file. Fallback: use the per-lesson `*_moodle.html` files — one Page activity per lesson.
- **Diagrams render without colors.** Moodle may be stripping the `<style>` block. Check your user role has trusted-content / extended HTML enabled.
- **Images broken.** Should not happen — images are base64-embedded. If it does, the wrong file was pasted (probably `lessons/01_*.html` instead of `lessons/01_*_moodle.html`).
"""


def infer_module_title(module_dir: Path) -> str:
    """Look at module_structure.json or fall back to the folder name."""
    structure = module_dir / "module_structure.json"
    if structure.is_file():
        try:
            import json
            data = json.loads(structure.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("module_title"):
                return data["module_title"]
        except Exception:
            pass
    return module_dir.name.replace("-", " ").title()


def write_readme(module_dir: Path) -> Path:
    out = module_dir / "README.md"
    title = infer_module_title(module_dir)
    out.write_text(
        README_TEMPLATE.format(module_title=title, module_folder=module_dir.name),
        encoding="utf-8",
    )
    return out


def run(module_dir: Path, build_mbz: bool = False) -> None:
    if not module_dir.is_dir():
        raise SystemExit(f"Module folder not found: {module_dir}")

    print(f"Finalizing {module_dir}")

    print("\n[1/4] Combining per-lesson quiz XMLs ...")
    combined_xml = combine_quiz_xmls(module_dir)
    print(f"      -> {combined_xml.name}" if combined_xml else "      (no quiz files)")

    print("\n[2/4] Embedding local images as base64 data URIs ...")
    embed_run(module_dir)

    print("\n[3/4] Building module_combined_moodle.html ...")
    combined = build_combined(module_dir)
    print(f"      -> {combined.name}  ({combined.stat().st_size/1024:,.0f} KB)")

    print("\n[4/4] Writing README.md and (if needed) IMAGES_TO_SOURCE.md ...")
    write_readme(module_dir)
    items = collect_image_requests(module_dir)
    out = write_images_to_source(module_dir, items)
    if out:
        print(f"      flagged {len(items)} image(s) in {out.name}")
    else:
        print("      no image-needed placeholders remain")

    if build_mbz:
        print("\n[+] Building single-module .mbz ...")
        from build_mbz import build_module  # local import; same pipeline/ dir
        out = build_module(module_dir)
        print(f"      -> {out.name}")

    print("\nDone. Upload using the instructions in the module's README.md.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--module", required=True,
                   help="Path to the module folder the agent wrote into.")
    p.add_argument("--mbz", action="store_true",
                   help="Also build a single-module .mbz (Moodle backup) after finalizing.")
    args = p.parse_args()
    run(Path(args.module), build_mbz=args.mbz)


if __name__ == "__main__":
    main()
