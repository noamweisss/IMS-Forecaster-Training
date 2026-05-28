#!/usr/bin/env python3
"""
build_mbz.py — Turn finalized course content into an importable Moodle backup
(`.mbz`) that restores the whole course in a single upload.

Pure Python, stdlib only. No LLM, no API key. This is an optional fourth step
after the existing pipeline:

    1. extract_sources.py    -> _extraction.json        (Python)
    2. <agent>               -> lesson HTML + quiz XML
    3. finalize_module.py    -> *_moodle.html + quiz XML (images base64-embedded)
    4. build_mbz.py          -> <course>.mbz             (this script)

Layout of the restored course: one section per module, each laid out as
overview Page -> (lesson Page -> lesson Quiz) for every lesson. See
docs/mbz_format.md for the schema this targets (Moodle 5.2+, backup_version
2026042000).

Usage:
    python pipeline/build_mbz.py --course courses/aviation-weather
    # -> courses/aviation-weather/aviation-weather.mbz
"""

from __future__ import annotations

import argparse
import json
import re
import tarfile
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(HERE))

from mbz.activities import build_page_activity, build_quiz_activity, QuestionInstance
from mbz.ids import IdAllocator
from mbz.quiz_to_backup import Question, parse_quiz_file
from mbz.structure import (
    ActivityRef, SectionRef, QuizSpec,
    build_course_files, build_gradebook_xml, build_moodle_backup_xml,
    build_question_bank, build_section_files,
)
from mbz import templates as T


# --------------------------------------------------------------------------- #
# Reading finalized course content                                            #
# --------------------------------------------------------------------------- #

@dataclass
class LessonContent:
    title: str
    page_html: str
    questions: list[Question] = field(default_factory=list)


@dataclass
class ModuleContent:
    title: str
    overview_html: str | None
    lessons: list[LessonContent] = field(default_factory=list)


def _title_from_filename(path: Path) -> str:
    stem = re.sub(r"_moodle$", "", path.stem)
    stem = re.sub(r"^\d+_", "", stem)
    return stem.replace("_", " ").title()


def read_module(module_dir: Path) -> ModuleContent:
    if not module_dir.is_dir():
        raise SystemExit(f"Module folder not found: {module_dir}")

    structure_path = module_dir / "module_structure.json"
    structure = {}
    if structure_path.is_file():
        structure = json.loads(structure_path.read_text(encoding="utf-8"))
    module_title = structure.get("module_title") or module_dir.name.replace("-", " ").title()
    lesson_titles = [l.get("lesson_title", "") for l in structure.get("lessons", [])]

    overview_path = module_dir / "00_module_overview_moodle.html"
    overview_html = overview_path.read_text(encoding="utf-8") if overview_path.is_file() else None

    lessons: list[LessonContent] = []
    lessons_dir = module_dir / "lessons"
    page_files = sorted(lessons_dir.glob("*_moodle.html")) if lessons_dir.is_dir() else []
    for i, pf in enumerate(page_files):
        title = lesson_titles[i] if i < len(lesson_titles) and lesson_titles[i] else _title_from_filename(pf)
        quiz_path = pf.with_name(pf.name.replace("_moodle.html", "_quiz.xml"))
        questions = parse_quiz_file(quiz_path) if quiz_path.is_file() else []
        lessons.append(LessonContent(title=title, page_html=pf.read_text(encoding="utf-8"),
                                     questions=questions))
    return ModuleContent(title=module_title, overview_html=overview_html, lessons=lessons)


def read_course(course_dir: Path) -> tuple[dict, list[ModuleContent]]:
    course_json = course_dir / "course.json"
    if not course_json.is_file():
        raise SystemExit(f"course.json not found in {course_dir}")
    meta = json.loads(course_json.read_text(encoding="utf-8"))
    modules: list[ModuleContent] = []
    for m in meta.get("modules", []):
        folder = course_dir / m.get("folder", f"module-{m.get('number')}")
        if not folder.is_dir():
            print(f"  (skipping {folder.name}: not found)")
            continue
        mc = read_module(folder)
        # Prefer the course.json title if the module didn't carry one.
        if m.get("title"):
            mc.title = m["title"]
        modules.append(mc)
    return meta, modules


# --------------------------------------------------------------------------- #
# Assembly                                                                     #
# --------------------------------------------------------------------------- #

def assemble(*, shortname: str, fullname: str, modules: list[ModuleContent],
             filename: str) -> dict[str, str]:
    """Build the complete set of {archive_path: content} files for a backup
    containing the given modules (one section each)."""
    ids = IdAllocator()
    ts = int(time.time())

    courseid = ids.next("course")
    course_contextid = ids.next("context")
    grade_category_id = ids.next("gradecategory")
    course_item_id = ids.next("gradeitem")

    files: dict[str, str] = {}
    sections: list[SectionRef] = []
    activities: list[ActivityRef] = []
    quiz_plans: list[dict] = []

    # Section 0 (General) is always present and empty.
    sections.append(SectionRef(ids.next("section"), 0, None, []))

    for m_index, module in enumerate(modules, start=1):
        sec_id = ids.next("section")
        seq: list[int] = []

        if module.overview_html:
            cmid = ids.next("cmid")
            name = f"{module.title} — Overview"
            files.update(build_page_activity(
                cmid=cmid, instance_id=ids.next("instance"), contextid=ids.next("context"),
                sectionid=sec_id, sectionnumber=m_index, name=name,
                content_html=module.overview_html, timestamp=ts))
            activities.append(ActivityRef(cmid, sec_id, "page", name))
            seq.append(cmid)

        for lesson in module.lessons:
            cmid = ids.next("cmid")
            files.update(build_page_activity(
                cmid=cmid, instance_id=ids.next("instance"), contextid=ids.next("context"),
                sectionid=sec_id, sectionnumber=m_index, name=lesson.title,
                content_html=lesson.page_html, timestamp=ts))
            activities.append(ActivityRef(cmid, sec_id, "page", lesson.title))
            seq.append(cmid)

            if lesson.questions:
                qcmid = ids.next("cmid")
                qname = f"{lesson.title} — Quiz"
                spec = QuizSpec(cmid=qcmid, contextid=ids.next("context"),
                                name=qname, questions=lesson.questions)
                quiz_plans.append({
                    "cmid": qcmid, "instance": ids.next("instance"),
                    "sectionid": sec_id, "sectionnumber": m_index, "spec": spec,
                    "grade_item_id": ids.next("gradeitem"),
                    "feedback_id": ids.next("feedback"),
                    "quiz_section_id": ids.next("quizsection"),
                })
                activities.append(ActivityRef(qcmid, sec_id, "quiz", qname))
                seq.append(qcmid)

        sections.append(SectionRef(sec_id, m_index, module.title, seq))

    # Question bank (fills each spec's category ids + qbe ids).
    specs = [qp["spec"] for qp in quiz_plans]
    files["questions.xml"] = build_question_bank(specs, ids, ts) if specs else \
        T.XML_DECL + "<question_categories>\n</question_categories>"

    # Quiz activities now that qbe ids exist.
    for qp in quiz_plans:
        spec = qp["spec"]
        qinstances = [
            QuestionInstance(instance_id=ids.next("qinstance"),
                             reference_id=ids.next("qreference"),
                             slot=i + 1, qbe_id=qbe)
            for i, qbe in enumerate(spec.qbe_ids)
        ]
        grademax = float(len(spec.questions)) or 1.0
        files.update(build_quiz_activity(
            cmid=qp["cmid"], instance_id=qp["instance"], contextid=spec.contextid,
            sectionid=qp["sectionid"], sectionnumber=qp["sectionnumber"],
            name=spec.name, intro_html="", timestamp=ts,
            question_instances=qinstances, grade_item_id=qp["grade_item_id"],
            grade_category_id=grade_category_id, feedback_id=qp["feedback_id"],
            quiz_section_id=qp["quiz_section_id"],
            question_category_ids=[spec.top_category_id, spec.default_category_id],
            grademax=grademax))

    for s in sections:
        files.update(build_section_files(s, ts))
    files.update(build_course_files(courseid=courseid, contextid=course_contextid,
                                    shortname=shortname, fullname=fullname, timestamp=ts))
    files["gradebook.xml"] = build_gradebook_xml(
        grade_category_id=grade_category_id, course_item_id=course_item_id, timestamp=ts)
    files.update(T.TOP_COMMON_FILES)
    files["moodle_backup.xml"] = build_moodle_backup_xml(
        filename=filename, courseid=courseid, course_shortname=shortname,
        course_fullname=fullname, course_contextid=course_contextid,
        activities=activities, sections=sections, timestamp=ts)
    files["moodle_backup.log"] = ""
    return files


# --------------------------------------------------------------------------- #
# Packaging                                                                    #
# --------------------------------------------------------------------------- #

def _archive_index(files: dict[str, str], timestamp: int) -> str:
    """Build the .ARCHIVE_INDEX: directories before files, with byte sizes."""
    dirs: set[str] = set()
    for path in files:
        parts = path.split("/")
        for i in range(1, len(parts)):
            dirs.add("/".join(parts[:i]) + "/")

    entries: list[str] = []
    items = sorted(set(files) | dirs)
    for item in items:
        if item.endswith("/"):
            entries.append(f"{item}\td\t0\t?")
        else:
            size = len(files[item].encode("utf-8"))
            entries.append(f"{item}\tf\t{size}\t{timestamp}")
    header = f"Moodle archive file index. Count: {len(entries)}"
    return header + "\n" + "\n".join(entries) + "\n"


def package(files: dict[str, str], output: Path, timestamp: int) -> Path:
    """Write `files` (plus a generated .ARCHIVE_INDEX) into a gzipped tar `.mbz`."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        for path, content in files.items():
            dest = tmpdir / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
        index = _archive_index(files, timestamp)
        (tmpdir / ".ARCHIVE_INDEX").write_text(index, encoding="utf-8")

        # Order: dirs before their contents, .ARCHIVE_INDEX first, log last.
        dirs: set[str] = set()
        for path in files:
            parts = path.split("/")
            for i in range(1, len(parts)):
                dirs.add("/".join(parts[:i]))
        ordered = [".ARCHIVE_INDEX"] + sorted(dirs | set(files))

        with tarfile.open(output, "w:gz") as tar:
            for arc in ordered:
                full = tmpdir / arc
                ti = tar.gettarinfo(str(full), arcname=arc)
                ti.mtime = timestamp
                ti.uid = ti.gid = 0
                ti.uname = ti.gname = ""
                if ti.isdir():
                    tar.addfile(ti)
                else:
                    with open(full, "rb") as fh:
                        tar.addfile(ti, fh)
    return output


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #

def build_course(course_dir: Path, output: Path | None = None) -> Path:
    meta, modules = read_course(course_dir)
    if not modules:
        raise SystemExit("No modules with content found.")
    course_id = meta.get("course_id", course_dir.name)
    fullname = meta.get("title", course_id)
    out = output or (course_dir / f"{course_id}.mbz")
    print(f"Building course backup: {fullname}")
    for m in modules:
        nq = sum(len(l.questions) for l in m.lessons)
        print(f"  - {m.title}: {len(m.lessons)} lesson(s), {nq} question(s)")
    files = assemble(shortname=course_id, fullname=fullname, modules=modules,
                     filename=out.name)
    ts = int(time.time())
    package(files, out, ts)
    print(f"\nWrote {out}  ({out.stat().st_size / 1024:,.0f} KB, {len(files)} files)")
    print("Restore it in Moodle: Course → Restore → upload → Merge into this course.")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--course", help="Path to a course folder (containing course.json).")
    p.add_argument("--output", help="Output .mbz path (optional).")
    args = p.parse_args()
    if not args.course:
        p.error("provide --course <course-folder>")
    build_course(Path(args.course), Path(args.output) if args.output else None)


if __name__ == "__main__":
    main()
