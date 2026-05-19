#!/usr/bin/env python3
"""
extract_sources.py — Read PPTX/PDF/DOCX source files and emit a single
JSON dump containing every slide, page, and section's text content.

Pure Python. No LLM. No API key needed. Run this before handing the
content over to a Claude Code agent for lesson generation — the agent
reads the JSON instead of opening binary files itself.

Usage:
    python pipeline/extract_sources.py \
        --input  courses/aviation-weather/source_files/module-2 \
        --output courses/aviation-weather/module-2/_extraction.json

The JSON shape matches what `module_pipeline.py` used internally so the
downstream agent prompts and assembly scripts can stay the same.
"""

import argparse
import json
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False

try:
    import fitz  # PyMuPDF
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


def extract_pptx(filepath: Path) -> dict:
    if not HAS_PPTX:
        return {"filename": filepath.name, "format": "pptx",
                "error": "python-pptx not installed", "slides": []}

    prs    = Presentation(filepath)
    slides = []

    for i, slide in enumerate(prs.slides):
        sd = {
            "slide_number": i + 1,
            "title":        "",
            "body":         [],
            "notes":        "",
            "has_images":   False,
            "has_charts":   False,
        }

        for shape in slide.shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                sd["has_images"] = True
            if getattr(shape, "has_chart", False):
                sd["has_charts"] = True
            if not shape.has_text_frame:
                continue

            raw_text = shape.text_frame.text.strip()
            if not raw_text:
                continue

            is_title = (
                shape.name == "Title"
                or (
                    getattr(shape, "is_placeholder", False)
                    and shape.placeholder_format.idx == 0
                )
            )

            if is_title:
                sd["title"] = raw_text
            else:
                for para in shape.text_frame.paragraphs:
                    t = para.text.strip()
                    if t:
                        sd["body"].append({"level": para.level, "text": t})

        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes and "Click to edit" not in notes:
                sd["notes"] = notes

        slides.append(sd)

    return {
        "filename":    filepath.name,
        "format":      "pptx",
        "slide_count": len(slides),
        "slides":      slides,
    }


def extract_pdf(filepath: Path) -> dict:
    if not HAS_PDF:
        return {"filename": filepath.name, "format": "pdf",
                "error": "PyMuPDF not installed", "pages": []}

    doc   = fitz.open(str(filepath))
    pages = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("blocks")
        images = page.get_images()

        title     = ""
        body_list = []

        for block in blocks:
            if len(block) >= 5:
                txt = block[4].strip()
                if txt:
                    if not title:
                        title = txt[:120]
                    else:
                        body_list.append(txt[:600])

        pages.append({
            "page_number": page_num + 1,
            "title":       title,
            "body":        body_list,
            "has_images":  len(images) > 0,
        })

    doc.close()

    return {
        "filename":   filepath.name,
        "format":     "pdf",
        "page_count": len(pages),
        "pages":      pages,
    }


def extract_docx(filepath: Path) -> dict:
    if not HAS_DOCX:
        return {"filename": filepath.name, "format": "docx",
                "error": "python-docx not installed", "sections": []}

    doc      = DocxDocument(filepath)
    sections = []
    current  = {"heading": filepath.stem, "paragraphs": [], "has_tables": False}

    for para in doc.paragraphs:
        txt = para.text.strip()
        if not txt:
            continue
        if para.style.name.startswith("Heading"):
            if current["paragraphs"]:
                sections.append(current)
            current = {"heading": txt, "paragraphs": [], "has_tables": False}
        else:
            current["paragraphs"].append(txt)

    for _ in doc.tables:
        current["has_tables"] = True

    if current["paragraphs"] or current["heading"] != filepath.stem:
        sections.append(current)

    return {
        "filename":      filepath.name,
        "format":        "docx",
        "section_count": len(sections),
        "sections":      sections,
    }


def extract_file(filepath: Path) -> dict:
    ext = filepath.suffix.lower()
    if ext == ".pptx":
        return extract_pptx(filepath)
    if ext == ".pdf":
        return extract_pdf(filepath)
    if ext in (".docx", ".doc"):
        return extract_docx(filepath)
    return {"filename": filepath.name, "error": f"Unsupported format: {ext}"}


def extract_all(input_dir: Path) -> list[dict]:
    supported = {".pptx", ".pdf", ".docx", ".doc"}
    files = sorted(f for f in input_dir.iterdir()
                   if f.is_file() and f.suffix.lower() in supported)

    print(f"Found {len(files)} source file(s) in {input_dir}:")
    for f in files:
        print(f"  {f.suffix.upper()[1:]:5}  {f.name}")

    results = []
    for f in files:
        print(f"  extracting {f.name} ...", end=" ", flush=True)
        results.append(extract_file(f))
        print("done")

    return results


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True,
                   help="Folder containing the source PPTX/PDF/DOCX files.")
    p.add_argument("--output", required=True,
                   help="Output JSON path (typically <module>/_extraction.json).")
    args = p.parse_args()

    in_dir = Path(args.input)
    if not in_dir.is_dir():
        raise SystemExit(f"Input folder not found: {in_dir}")

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    extracted = extract_all(in_dir)
    with out.open("w", encoding="utf-8") as f:
        json.dump(extracted, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {out}  ({len(extracted)} file(s) extracted)")


if __name__ == "__main__":
    main()
