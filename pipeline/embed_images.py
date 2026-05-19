#!/usr/bin/env python3
"""
embed_images.py — Inline locally-stored images as base64 data URIs.

Why: Moodle does not preserve relative <img src="images/foo.png"> paths
when HTML is pasted into a Page or restored from a backup. We sidestep
the whole pluginfile.php / @@PLUGINFILE@@ dance by embedding the image
bytes directly into the HTML as `data:image/png;base64,...`.

Usage:
    python pipeline/embed_images.py --module courses/aviation-weather/module-1

What it does:
    1. Walks <module>/lessons/*_moodle.html and the module overview.
    2. For each <img src="..."> tag whose src resolves to a local file
       under the lessons/Images/ folder (or lessons/images/), replaces
       the src attribute with a data: URI.
    3. Rewrites the same files in place. Idempotent — already-embedded
       data: URIs are left alone.

Why a separate script and not part of module_pipeline.py:
    Image sourcing happens after the pipeline runs — a human reviews the
    IMAGES_TO_SOURCE.md list, finds appropriate photos, and saves them
    into lessons/Images/. Embedding has to happen *after* the human step,
    so it lives on its own and can be re-run when more images arrive.
"""

import argparse
import base64
import mimetypes
import re
from pathlib import Path


IMG_TAG_RE = re.compile(
    r'(<img\b[^>]*\bsrc=)(["\'])([^"\']+)\2',
    re.IGNORECASE,
)


def _data_uri(image_path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(image_path))
    if not mime:
        # Reasonable default for the file types we use (png / jpg / webp).
        mime = "application/octet-stream"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _resolve_image_src(src: str, html_file: Path, images_dirs: list[Path]) -> Path | None:
    """Return the local file the src refers to, or None if it can't be
    resolved. Skips already-embedded data: URIs and external http(s) URLs."""
    if src.startswith(("data:", "http://", "https://", "//")):
        return None

    # Try relative to the HTML file's directory first.
    candidate = (html_file.parent / src).resolve()
    if candidate.is_file():
        return candidate

    # Then try the configured images dirs by basename.
    name = Path(src).name
    for d in images_dirs:
        candidate = (d / name).resolve()
        if candidate.is_file():
            return candidate

    return None


def embed_in_html(html_file: Path, images_dirs: list[Path]) -> tuple[int, int]:
    """Embed every resolvable <img src> in `html_file`. Returns a tuple of
    (images_embedded, images_unresolved)."""
    text = html_file.read_text(encoding="utf-8")
    embedded = 0
    unresolved = 0

    def repl(match: re.Match) -> str:
        nonlocal embedded, unresolved
        prefix, quote, src = match.group(1), match.group(2), match.group(3)
        resolved = _resolve_image_src(src, html_file, images_dirs)
        if resolved is None:
            if not src.startswith(("data:", "http://", "https://", "//")):
                unresolved += 1
            return match.group(0)
        uri = _data_uri(resolved)
        embedded += 1
        return f"{prefix}{quote}{uri}{quote}"

    new_text = IMG_TAG_RE.sub(repl, text)
    if new_text != text:
        html_file.write_text(new_text, encoding="utf-8")
    return embedded, unresolved


def run(module_dir: Path) -> None:
    lessons_dir = module_dir / "lessons"
    if not lessons_dir.is_dir():
        raise SystemExit(f"No lessons/ folder under {module_dir}")

    # Allow either "Images" or "images" (the pilot used both at different times).
    images_dirs = [d for d in (lessons_dir / "Images", lessons_dir / "images")
                   if d.is_dir()]

    targets = sorted(lessons_dir.glob("*_moodle.html"))
    overview = module_dir / "00_module_overview_moodle.html"
    if overview.is_file():
        targets.append(overview)

    if not targets:
        print(f"No *_moodle.html files found under {module_dir}")
        return

    total_embedded = 0
    total_unresolved = 0
    for f in targets:
        e, u = embed_in_html(f, images_dirs)
        total_embedded += e
        total_unresolved += u
        status = f"  +{e}"
        if u:
            status += f"  (?{u} unresolved)"
        print(f"  {f.relative_to(module_dir)}{status}")

    print(f"\nEmbedded {total_embedded} image(s).")
    if total_unresolved:
        print(f"WARNING: {total_unresolved} <img> tag(s) had a src that could not be "
              "resolved to a local file. They were left as-is.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--module", required=True,
                   help="Path to a generated module directory "
                        "(e.g. courses/aviation-weather/module-1).")
    args = p.parse_args()
    run(Path(args.module))


if __name__ == "__main__":
    main()
