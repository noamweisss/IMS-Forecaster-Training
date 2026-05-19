#!/usr/bin/env python3
"""
validate_translation.py — Deterministic structural-parity checks for a
Hebrew translation of an IMS module.

Pure Python. No LLM. No API key. Runs as a preflight before the Gemini
editor agent, so the LLM editor only spends tokens on the things only an
LLM can judge (glossary consistency, residual English, hallucination,
quiz answer correctness semantics, Hebrew fluency).

What this script checks, per file pair (English vs Hebrew):

    1. structural_parity   element counts match (h1/h2/h3/p/li/table/tr/
                           figure/svg/figcaption/callout/image-needed/
                           question/answer)
    2. hex_preservation    sets of #RRGGBB codes identical
    3. css_class           sets of class="..." values identical
    4. cdata_integrity     CDATA block counts identical, no split/unwrapped
    5. rtl_markers         every .ims-lesson wrapper has dir="rtl" lang="he"
    6. svg_content         no var(--xxx) introduced into SVG attributes
    7. file_presence       every translatable English file has a Hebrew
                           counterpart; _translation_manifest.json present

Output: writes (or augments) <translation-module>/review.json with
issues marked `produced_by: "python"`. Pre-existing entries from the
Gemini editor (`produced_by: "gemini-3-pro"` or similar) are preserved.

Exit code: 0 if no `error`-severity issues; 1 if any.

Usage:
    python pipeline/validate_translation.py \
        --source-module      courses/aviation-weather/module-1 \
        --translation-module courses/aviation-weather/module-1-he

See docs/hebrew_translation_spec.md for the full review.json schema,
severity rubric, and category definitions.
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Regexes mirror the style in pipeline/build_combined_page.py.
_HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b")
_CLASS_RE = re.compile(r'\bclass="([^"]+)"')
_CDATA_RE = re.compile(r"<!\[CDATA\[.*?\]\]>", re.DOTALL)
_WRAPPER_OPEN_RE = re.compile(r'<div\s+class="ims-lesson"([^>]*)>')
_SVG_RE = re.compile(r"<svg\b.*?</svg>", re.DOTALL | re.IGNORECASE)
_VAR_IN_SVG_RE = re.compile(r"var\s*\(\s*--")
_QUESTION_RE = re.compile(r"<question\b", re.IGNORECASE)
_ANSWER_RE = re.compile(r"<answer\b", re.IGNORECASE)
_FRACTION_100_RE = re.compile(r'fraction="100"')

# Element tags we count for structural parity.
_COUNT_TAGS = [
    "h1", "h2", "h3", "p", "li", "table", "tr",
    "figure", "svg", "figcaption",
]


def _count_tag(html: str, tag: str) -> int:
    return len(re.findall(rf"<{tag}\b", html, re.IGNORECASE))


def _count_callouts(html: str) -> int:
    return len(re.findall(r'class="callout\b', html, re.IGNORECASE))


def _count_image_needed(html: str) -> int:
    return len(re.findall(r'class="image-needed"', html, re.IGNORECASE))


def _hex_codes(html: str) -> set[str]:
    return {m.upper() for m in _HEX_RE.findall(html)}


def _class_values(html: str) -> set[str]:
    out: set[str] = set()
    for raw in _CLASS_RE.findall(html):
        for token in raw.split():
            out.add(token)
    return out


def _issue(file: str, severity: str, category: str, message: str,
           english_excerpt=None, hebrew_excerpt=None,
           locator=None, suggested_fix=None) -> dict:
    return {
        "file": file,
        "locator": locator,
        "severity": severity,
        "category": category,
        "produced_by": "python",
        "english_excerpt": english_excerpt,
        "hebrew_excerpt": hebrew_excerpt,
        "message": message,
        "suggested_fix": suggested_fix,
    }


def _check_html_pair(rel: str, en: str, he: str) -> list[dict]:
    issues: list[dict] = []

    # 1. structural_parity
    for tag in _COUNT_TAGS:
        en_n, he_n = _count_tag(en, tag), _count_tag(he, tag)
        if en_n != he_n:
            issues.append(_issue(
                rel, "error", "structural_parity",
                f"Element count differs for <{tag}>: English has {en_n}, "
                f"Hebrew has {he_n}. Translator must preserve structure.",
                suggested_fix=f"Re-run the translator on this file; "
                              f"make sure no <{tag}> blocks were dropped or duplicated.",
            ))
    en_co, he_co = _count_callouts(en), _count_callouts(he)
    if en_co != he_co:
        issues.append(_issue(
            rel, "error", "structural_parity",
            f"Callout count differs: English has {en_co}, Hebrew has {he_co}.",
        ))
    en_in, he_in = _count_image_needed(en), _count_image_needed(he)
    if en_in != he_in:
        issues.append(_issue(
            rel, "error", "structural_parity",
            f"image-needed count differs: English has {en_in}, Hebrew has {he_in}.",
        ))

    # 2. hex_preservation
    en_hex, he_hex = _hex_codes(en), _hex_codes(he)
    if en_hex != he_hex:
        missing = sorted(en_hex - he_hex)
        added = sorted(he_hex - en_hex)
        msg = []
        if missing:
            msg.append(f"hex codes present in English but missing in Hebrew: {missing}")
        if added:
            msg.append(f"hex codes present in Hebrew but not in English: {added}")
        issues.append(_issue(
            rel, "error", "hex_preservation", "; ".join(msg),
            suggested_fix="Translator must preserve every hex code byte-for-byte. "
                          "Hex codes appear in <style> blocks, inline style attributes, "
                          "and SVG fill/stroke attributes.",
        ))

    # 3. css_class
    en_cls, he_cls = _class_values(en), _class_values(he)
    if en_cls != he_cls:
        missing = sorted(en_cls - he_cls)
        added = sorted(he_cls - en_cls)
        msg = []
        if missing:
            msg.append(f"CSS classes present in English but missing in Hebrew: {missing}")
        if added:
            msg.append(f"CSS classes present in Hebrew but not in English: {added}")
        issues.append(_issue(
            rel, "error", "css_class", "; ".join(msg),
            suggested_fix="Translator must never modify CSS class names.",
        ))

    # 5. rtl_markers — applies to lesson HTML, not quiz XML
    wrappers = _WRAPPER_OPEN_RE.findall(he)
    if not wrappers:
        issues.append(_issue(
            rel, "error", "rtl_markers",
            'No <div class="ims-lesson"> wrapper found in Hebrew file.',
            suggested_fix="Every translated lesson body fragment must wrap content "
                          'in <div class="ims-lesson" dir="rtl" lang="he">.',
        ))
    else:
        for attrs in wrappers:
            if 'dir="rtl"' not in attrs or 'lang="he"' not in attrs:
                issues.append(_issue(
                    rel, "error", "rtl_markers",
                    'ims-lesson wrapper is missing dir="rtl" or lang="he".',
                    hebrew_excerpt=f'<div class="ims-lesson"{attrs}>',
                    suggested_fix='Change the wrapper to '
                                  '<div class="ims-lesson" dir="rtl" lang="he">.',
                ))

    # 6. svg_content — no var(--xxx) inside any SVG block
    for svg_match in _SVG_RE.finditer(he):
        if _VAR_IN_SVG_RE.search(svg_match.group(0)):
            issues.append(_issue(
                rel, "error", "svg_content",
                "var(--xxx) reference found inside an SVG block in the Hebrew file.",
                hebrew_excerpt=svg_match.group(0)[:120] + "...",
                suggested_fix="Replace any var(--xxx) inside SVG attributes with the "
                              "literal hex code. Moodle strips the <style> block so "
                              "var() references render as black or invisible.",
            ))

    return issues


def _check_quiz_pair(rel: str, en: str, he: str) -> list[dict]:
    issues: list[dict] = []

    # 4. cdata_integrity
    en_cdata, he_cdata = len(_CDATA_RE.findall(en)), len(_CDATA_RE.findall(he))
    if en_cdata != he_cdata:
        issues.append(_issue(
            rel, "error", "cdata_integrity",
            f"CDATA block count differs: English has {en_cdata}, Hebrew has {he_cdata}.",
            suggested_fix="Translator must preserve every <![CDATA[ ... ]]> wrapper. "
                          "Translate the text inside the wrapper; never split or unwrap it.",
        ))

    # 1. structural_parity (quiz-specific)
    en_q, he_q = len(_QUESTION_RE.findall(en)), len(_QUESTION_RE.findall(he))
    if en_q != he_q:
        issues.append(_issue(
            rel, "error", "structural_parity",
            f"Question count differs: English has {en_q}, Hebrew has {he_q}.",
        ))
    en_a, he_a = len(_ANSWER_RE.findall(en)), len(_ANSWER_RE.findall(he))
    if en_a != he_a:
        issues.append(_issue(
            rel, "error", "structural_parity",
            f"Answer count differs: English has {en_a}, Hebrew has {he_a}.",
        ))
    en_f, he_f = len(_FRACTION_100_RE.findall(en)), len(_FRACTION_100_RE.findall(he))
    if en_f != he_f:
        issues.append(_issue(
            rel, "error", "quiz_correctness",
            f'fraction="100" count differs: English has {en_f}, Hebrew has {he_f}. '
            "Every question must have exactly one correct answer.",
        ))

    return issues


def _walk_module(module_dir: Path) -> dict[str, Path]:
    """Return {relative_path: absolute_path} for translatable files."""
    files: dict[str, Path] = {}
    for path in sorted(module_dir.rglob("*")):
        if not path.is_file():
            continue
        name = path.name
        if name.endswith("_moodle.html") or name.endswith("_quiz.xml"):
            files[str(path.relative_to(module_dir))] = path
    return files


def validate(source_module: Path, translation_module: Path) -> tuple[list[dict], dict]:
    issues: list[dict] = []

    source_files = _walk_module(source_module)
    translation_files = _walk_module(translation_module)

    # 7. file_presence
    for rel in source_files:
        if rel not in translation_files:
            issues.append(_issue(
                rel, "error", "file_presence",
                "English file has no Hebrew counterpart at the same relative path.",
                suggested_fix=f"Re-run the translator to produce "
                              f"{translation_module}/{rel}.",
            ))

    manifest_path = translation_module / "_translation_manifest.json"
    if not manifest_path.exists():
        issues.append(_issue(
            "_translation_manifest.json", "error", "file_presence",
            "Translator manifest is missing.",
            suggested_fix="Re-run the translator. The manifest is the last file it writes.",
        ))
    else:
        try:
            json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(_issue(
                "_translation_manifest.json", "error", "file_presence",
                f"Translator manifest does not parse as valid JSON: {exc}.",
            ))

    # Pairwise content checks
    for rel, en_path in source_files.items():
        he_path = translation_files.get(rel)
        if he_path is None:
            continue
        en = en_path.read_text(encoding="utf-8")
        he = he_path.read_text(encoding="utf-8")
        if rel.endswith("_moodle.html"):
            issues.extend(_check_html_pair(rel, en, he))
        elif rel.endswith("_quiz.xml"):
            issues.extend(_check_quiz_pair(rel, en, he))

    summary = {
        "files_reviewed": len(translation_files),
        "error_count": sum(1 for i in issues if i["severity"] == "error"),
        "warning_count": sum(1 for i in issues if i["severity"] == "warning"),
        "info_count": sum(1 for i in issues if i["severity"] == "info"),
    }
    return issues, summary


def _archive_existing(review_path: Path) -> None:
    if not review_path.exists():
        return
    archive_dir = review_path.parent / ".archive"
    archive_dir.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    shutil.copy2(review_path, archive_dir / f"review_{stamp}.json")


def _merge_with_existing(review_path: Path, new_issues: list[dict]) -> list[dict]:
    """Keep non-Python entries from any existing review.json; replace Python ones."""
    if not review_path.exists():
        return new_issues
    try:
        existing = json.loads(review_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return new_issues
    kept = [i for i in existing.get("issues", []) if i.get("produced_by") != "python"]
    return kept + new_issues


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument("--source-module", required=True, type=Path,
                   help="English module folder, e.g. courses/aviation-weather/module-1")
    p.add_argument("--translation-module", required=True, type=Path,
                   help="Hebrew module folder, e.g. courses/aviation-weather/module-1-he")
    args = p.parse_args()

    src = args.source_module.resolve()
    tgt = args.translation_module.resolve()

    if not src.is_dir():
        print(f"error: source module not found: {src}", file=sys.stderr)
        return 2
    if not tgt.is_dir():
        print(f"error: translation module not found: {tgt}", file=sys.stderr)
        return 2

    new_issues, _ = validate(src, tgt)
    review_path = tgt / "review.json"
    _archive_existing(review_path)
    merged = _merge_with_existing(review_path, new_issues)
    summary = {
        "files_reviewed": len(_walk_module(tgt)),
        "error_count": sum(1 for i in merged if i["severity"] == "error"),
        "warning_count": sum(1 for i in merged if i["severity"] == "warning"),
        "info_count": sum(1 for i in merged if i["severity"] == "info"),
    }
    review = {
        "schema_version": "1.0",
        "editor_model": None,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_module": str(src),
        "translation_module": str(tgt),
        "summary": summary,
        "issues": merged,
    }
    review_path.write_text(json.dumps(review, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"validate_translation: reviewed {summary['files_reviewed']} files; "
          f"{summary['error_count']} error, "
          f"{summary['warning_count']} warning, "
          f"{summary['info_count']} info "
          f"(wrote {review_path})")

    return 1 if summary["error_count"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
