#!/usr/bin/env python3
"""
build_combined_page.py — Concatenate a module's per-lesson Moodle fragments
into a single HTML file that can be pasted into Moodle as ONE Page activity.

Input:  a generated module folder containing
            00_module_overview_moodle.html
            lessons/NN_<slug>_moodle.html  (multiple)

Output: <module>/module_combined_moodle.html

Why one big page per module instead of one Page per lesson:
    The user uploads one paste per module instead of five. The HTML is
    self-contained (images base64-embedded, CSS scoped to .ims-lesson, SVG
    colors literal hex), so it survives Moodle's HTML editor.

    Students see the overview at the top, a sticky table of contents listing
    every lesson, then each lesson stacked as a <section> with anchor links
    from the TOC. Quizzes remain a separate Moodle activity imported from
    the module's quiz XML — keeping quiz tracking real instead of
    JavaScript-only.

Usage:
    python pipeline/build_combined_page.py --module courses/aviation-weather/module-1
"""

import argparse
import re
from pathlib import Path


_STYLE_RE   = re.compile(r"<style\b[^>]*>.*?</style>", re.DOTALL | re.IGNORECASE)
_WRAPPER_RE = re.compile(
    r'<div\s+class="ims-lesson"[^>]*>(.*)</div>\s*$',
    re.DOTALL | re.IGNORECASE,
)
_BREADCRUMB_RE = re.compile(
    r'<p\s+class="breadcrumb"[^>]*>.*?</p>',
    re.DOTALL | re.IGNORECASE,
)


def _split_style_and_body(html: str) -> tuple[str, str]:
    """Return (style_block, body_html) for a fragment file."""
    style_match = _STYLE_RE.search(html)
    style = style_match.group(0) if style_match else ""
    without_style = _STYLE_RE.sub("", html).strip()
    wrapper_match = _WRAPPER_RE.search(without_style)
    body = wrapper_match.group(1).strip() if wrapper_match else without_style
    return style, body


def _slug_from_filename(name: str) -> str:
    # Strip leading digits + underscore and the trailing _moodle.html suffix.
    stem = re.sub(r"_moodle\.html$", "", name)
    stem = re.sub(r"^\d+_", "", stem)
    return stem


def build_combined(module_dir: Path) -> Path:
    overview_file = module_dir / "00_module_overview_moodle.html"
    lessons_dir   = module_dir / "lessons"
    lesson_files  = sorted(lessons_dir.glob("*_moodle.html"))

    if not overview_file.is_file():
        raise SystemExit(f"Missing overview fragment: {overview_file}")
    if not lesson_files:
        raise SystemExit(f"No lesson fragments found in {lessons_dir}")

    style, overview_body = _split_style_and_body(
        overview_file.read_text(encoding="utf-8")
    )
    # Drop the overview's own breadcrumb — the combined page has its own header.
    overview_body = _BREADCRUMB_RE.sub("", overview_body, count=1).strip()

    lessons = []
    for f in lesson_files:
        _, body = _split_style_and_body(f.read_text(encoding="utf-8"))
        body = _BREADCRUMB_RE.sub("", body, count=1).strip()
        # Extract the lesson's <h1>...</h1> for the TOC label and section anchor.
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.DOTALL | re.IGNORECASE)
        title = re.sub(r"<[^>]+>", "", h1_match.group(1)).strip() if h1_match else f.stem
        lessons.append({"file": f, "title": title, "body": body,
                        "slug": _slug_from_filename(f.name)})

    # Build the in-page table of contents.
    toc_items = "\n".join(
        f'    <li><a href="#lesson-{i}">Lesson {i}: {lesson["title"]}</a></li>'
        for i, lesson in enumerate(lessons, 1)
    )
    toc_html = (
        '<nav class="ims-toc" aria-label="Module contents">\n'
        '  <strong>In this module:</strong>\n'
        '  <ol>\n'
        '    <li><a href="#module-overview">Module overview</a></li>\n'
        f"{toc_items}\n"
        '  </ol>\n'
        '</nav>'
    )

    # Stack the lessons. Each gets a stable anchor and a horizontal rule above
    # it so visual separation survives even if Moodle's theme is bare.
    lesson_sections = []
    for i, lesson in enumerate(lessons, 1):
        lesson_sections.append(
            f'<hr class="ims-lesson-sep">\n'
            f'<section id="lesson-{i}" class="ims-lesson-section" '
            f'data-lesson-slug="{lesson["slug"]}">\n'
            f'{lesson["body"]}\n'
            f'</section>'
        )

    # Extra CSS for the combined-page-only chrome (TOC, lesson separators).
    extra_css = """
.ims-lesson .ims-toc { background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 1rem 1.5rem; margin: 1rem 0 2rem; }
.ims-lesson .ims-toc strong { display: block; margin-bottom: 0.5rem;
  font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--muted); }
.ims-lesson .ims-toc ol { margin: 0; padding-left: 1.4rem; }
.ims-lesson .ims-toc a { color: var(--accent); text-decoration: none; }
.ims-lesson .ims-toc a:hover { text-decoration: underline; }
.ims-lesson .ims-lesson-sep { border: 0; border-top: 2px solid var(--border);
  margin: 4rem 0 2rem; }
.ims-lesson .ims-lesson-section { scroll-margin-top: 1rem; }
""".strip()

    # Inject the extra CSS at the end of the existing <style> block.
    combined_style = re.sub(
        r"</style>\s*$",
        f"\n{extra_css}\n</style>",
        style,
        count=1,
    )

    parts = [
        combined_style,
        '<div class="ims-lesson">',
        '<section id="module-overview">',
        overview_body,
        '</section>',
        toc_html,
        *lesson_sections,
        '</div>',
    ]

    out = module_dir / "module_combined_moodle.html"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--module", required=True,
                   help="Path to a generated module folder.")
    args = p.parse_args()
    out = build_combined(Path(args.module))
    size_kb = out.stat().st_size / 1024
    print(f"Wrote {out}  ({size_kb:,.0f} KB)")


if __name__ == "__main__":
    main()
