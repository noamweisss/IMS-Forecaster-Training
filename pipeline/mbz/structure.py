#!/usr/bin/env python3
"""
structure.py — Assemble the course-level / structural XML of a .mbz:
moodle_backup.xml (the manifest), sections, course/course.xml, gradebook.xml,
and questions.xml (the whole question bank).

These are pure builders: give them ids + parsed content and they return XML
strings. The orchestrator (build_mbz.py) allocates ids, reads the module HTML
and quiz files, calls activities.py for the per-activity dirs and the functions
here for everything else, then hands the lot to packaging.

The quiz↔questions contextid invariant (docs/mbz_format.md) is realised here:
`build_question_bank` records, per quiz, the category ids and question-bank-entry
ids so the orchestrator can wire the quiz's question_instances and inforef to the
same contexts.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

try:
    from . import templates as T
    from .ids import IdAllocator, make_stamp
    from .quiz_to_backup import Question, build_question_element
except ImportError:  # run directly as a script
    import templates as T
    from ids import IdAllocator, make_stamp
    from quiz_to_backup import Question, build_question_element

CONTEXT_MODULE = 70  # Moodle CONTEXT_MODULE level


def _serialize(root: ET.Element) -> str:
    ET.indent(root, space="  ")
    return T.XML_DECL + ET.tostring(root, encoding="unicode")


def _sub(parent: ET.Element, tag: str, text: str | None = None) -> ET.Element:
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = text
    return el


# --------------------------------------------------------------------------- #
# Manifest description dataclasses                                             #
# --------------------------------------------------------------------------- #

@dataclass
class ActivityRef:
    cmid: int
    sectionid: int
    modulename: str          # "page" | "quiz"
    title: str

    @property
    def directory(self) -> str:
        return f"activities/{self.modulename}_{self.cmid}"


@dataclass
class SectionRef:
    sectionid: int
    number: int
    name: str | None
    sequence: list[int]      # cmids in display order

    @property
    def directory(self) -> str:
        return f"sections/section_{self.sectionid}"

    @property
    def title(self) -> str:
        return self.name if self.name else str(self.number)


@dataclass
class QuizSpec:
    """One quiz's questions, plus ids filled in by build_question_bank()."""
    cmid: int
    contextid: int
    name: str
    questions: list[Question]
    top_category_id: int = 0
    default_category_id: int = 0
    qbe_ids: list[int] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# sections                                                                     #
# --------------------------------------------------------------------------- #

def build_section_files(section: SectionRef, timestamp: int) -> dict[str, str]:
    root = ET.Element("section", {"id": str(section.sectionid)})
    _sub(root, "number", str(section.number))
    _sub(root, "name", section.name if section.name else "$@NULL@$")
    _sub(root, "summary", "")
    _sub(root, "summaryformat", "1")
    _sub(root, "sequence", ",".join(str(c) for c in section.sequence))
    _sub(root, "visible", "1")
    _sub(root, "availabilityjson", "$@NULL@$")
    _sub(root, "component", "$@NULL@$")
    _sub(root, "itemid", "$@NULL@$")
    _sub(root, "timemodified", str(timestamp))
    return {
        f"{section.directory}/section.xml": _serialize(root),
        f"{section.directory}/inforef.xml": T.SECTION_INFOREF_EMPTY,
    }


# --------------------------------------------------------------------------- #
# course/                                                                      #
# --------------------------------------------------------------------------- #

def build_course_files(
    *, courseid: int, contextid: int, shortname: str, fullname: str,
    timestamp: int,
) -> dict[str, str]:
    root = ET.Element("course", {"id": str(courseid), "contextid": str(contextid)})
    _sub(root, "shortname", shortname)
    _sub(root, "fullname", fullname)
    _sub(root, "idnumber", "")
    _sub(root, "summary", "")
    _sub(root, "summaryformat", "1")
    _sub(root, "format", "topics")
    _sub(root, "showgrades", "1")
    _sub(root, "newsitems", "5")
    _sub(root, "startdate", "0")
    _sub(root, "enddate", "0")
    _sub(root, "marker", "0")
    _sub(root, "maxbytes", "0")
    _sub(root, "legacyfiles", "0")
    _sub(root, "showreports", "0")
    _sub(root, "visible", "1")
    _sub(root, "groupmode", "0")
    _sub(root, "groupmodeforce", "0")
    _sub(root, "defaultgroupingid", "0")
    _sub(root, "lang", "")
    _sub(root, "theme", "")
    _sub(root, "timecreated", str(timestamp))
    _sub(root, "timemodified", str(timestamp))
    _sub(root, "requested", "0")
    _sub(root, "showactivitydates", "1")
    _sub(root, "showcompletionconditions", "1")
    _sub(root, "pdfexportfont", "$@NULL@$")
    _sub(root, "enablecompletion", "1")
    _sub(root, "completionnotify", "0")
    _sub(root, "enableaitools", "$@NULL@$")
    cat = ET.SubElement(root, "category", {"id": "1"})
    _sub(cat, "name", "Category 1")
    _sub(cat, "description", "$@NULL@$")
    _sub(root, "tags")
    _sub(root, "customfields")
    cfo = _sub(root, "courseformatoptions")
    for name, value in (("hiddensections", "1"), ("coursedisplay", "0")):
        opt = _sub(cfo, "courseformatoption")
        _sub(opt, "format", "topics")
        _sub(opt, "sectionid", "0")
        _sub(opt, "name", name)
        _sub(opt, "value", value)

    files = {"course/course.xml": _serialize(root)}
    files.update({f"course/{name}": content
                  for name, content in T.COURSE_COMMON_FILES.items()})
    return files


# --------------------------------------------------------------------------- #
# gradebook.xml (course level)                                                 #
# --------------------------------------------------------------------------- #

def build_gradebook_xml(
    *, grade_category_id: int, course_item_id: int, timestamp: int,
) -> str:
    root = ET.Element("gradebook")
    _sub(root, "attributes")
    cats = _sub(root, "grade_categories")
    cat = ET.SubElement(cats, "grade_category", {"id": str(grade_category_id)})
    _sub(cat, "parent", "$@NULL@$")
    _sub(cat, "depth", "1")
    _sub(cat, "path", f"/{grade_category_id}/")
    _sub(cat, "fullname", "?")
    _sub(cat, "aggregation", "13")
    _sub(cat, "keephigh", "0")
    _sub(cat, "droplow", "0")
    _sub(cat, "aggregateonlygraded", "1")
    _sub(cat, "aggregateoutcomes", "0")
    _sub(cat, "timecreated", str(timestamp))
    _sub(cat, "timemodified", str(timestamp))
    _sub(cat, "hidden", "0")

    items = _sub(root, "grade_items")
    gi = ET.SubElement(items, "grade_item", {"id": str(course_item_id)})
    _sub(gi, "categoryid", "$@NULL@$")
    _sub(gi, "itemname", "$@NULL@$")
    _sub(gi, "itemtype", "course")
    _sub(gi, "itemmodule", "$@NULL@$")
    _sub(gi, "iteminstance", str(grade_category_id))
    _sub(gi, "itemnumber", "$@NULL@$")
    _sub(gi, "iteminfo", "$@NULL@$")
    _sub(gi, "idnumber", "$@NULL@$")
    _sub(gi, "calculation", "$@NULL@$")
    _sub(gi, "gradetype", "1")
    _sub(gi, "grademax", "100.00000")
    _sub(gi, "grademin", "0.00000")
    _sub(gi, "scaleid", "$@NULL@$")
    _sub(gi, "outcomeid", "$@NULL@$")
    _sub(gi, "gradepass", "0.00000")
    _sub(gi, "multfactor", "1.00000")
    _sub(gi, "plusfactor", "0.00000")
    _sub(gi, "aggregationcoef", "0.00000")
    _sub(gi, "aggregationcoef2", "0.00000")
    _sub(gi, "weightoverride", "0")
    _sub(gi, "sortorder", "1")
    _sub(gi, "display", "0")
    _sub(gi, "decimals", "$@NULL@$")
    _sub(gi, "hidden", "0")
    _sub(gi, "locked", "0")
    _sub(gi, "locktime", "0")
    _sub(gi, "needsupdate", "0")
    _sub(gi, "timecreated", str(timestamp))
    _sub(gi, "timemodified", str(timestamp))
    _sub(gi, "grade_grades")
    _sub(root, "grade_letters")
    settings = _sub(root, "grade_settings")
    st = ET.SubElement(settings, "grade_setting", {"id": ""})
    _sub(st, "name", "minmaxtouse")
    _sub(st, "value", "1")
    return _serialize(root)


# --------------------------------------------------------------------------- #
# questions.xml (the whole question bank)                                      #
# --------------------------------------------------------------------------- #

def build_question_bank(
    quiz_specs: list[QuizSpec], ids: IdAllocator, timestamp: int, ownerid: int = 2,
) -> str:
    """Build questions.xml. Mutates each QuizSpec to record its category ids and
    question_bank_entry ids (the orchestrator needs them for quiz wiring)."""
    root = ET.Element("question_categories")
    for spec in quiz_specs:
        top_id = ids.next("category")
        default_id = ids.next("category")
        spec.top_category_id = top_id
        spec.default_category_id = default_id

        # 'top' category (empty container).
        top = ET.SubElement(root, "question_category", {"id": str(top_id)})
        _sub(top, "name", "top")
        _sub(top, "contextid", str(spec.contextid))
        _sub(top, "contextlevel", str(CONTEXT_MODULE))
        _sub(top, "contextinstanceid", str(spec.cmid))
        _sub(top, "info", "")
        _sub(top, "infoformat", "0")
        _sub(top, "stamp", make_stamp(ids.next("stampseq")))
        _sub(top, "parent", "0")
        _sub(top, "sortorder", "0")
        _sub(top, "idnumber", "$@NULL@$")
        _sub(top, "question_bank_entries")

        # 'Default for <quiz>' category holding the questions.
        default = ET.SubElement(root, "question_category", {"id": str(default_id)})
        _sub(default, "name", f"Default for {spec.name}")
        _sub(default, "contextid", str(spec.contextid))
        _sub(default, "contextlevel", str(CONTEXT_MODULE))
        _sub(default, "contextinstanceid", str(spec.cmid))
        _sub(default, "info",
             f"The default category for questions shared in context '{spec.name}'.")
        _sub(default, "infoformat", "0")
        _sub(default, "stamp", make_stamp(ids.next("stampseq")))
        _sub(default, "parent", str(top_id))
        _sub(default, "sortorder", "999")
        _sub(default, "idnumber", "$@NULL@$")
        entries = _sub(default, "question_bank_entries")

        for q in spec.questions:
            qbe_id = ids.next("qbe")
            spec.qbe_ids.append(qbe_id)
            entry = ET.SubElement(entries, "question_bank_entry", {"id": str(qbe_id)})
            _sub(entry, "questioncategoryid", str(default_id))
            _sub(entry, "idnumber", "$@NULL@$")
            _sub(entry, "ownerid", str(ownerid))
            _sub(entry, "nextversion", "2")
            version = _sub(entry, "question_version")
            versions = ET.SubElement(
                version, "question_versions", {"id": str(ids.next("qversion"))})
            _sub(versions, "version", "1")
            _sub(versions, "status", "ready")
            questions_el = _sub(versions, "questions")
            qel = build_question_element(
                q,
                question_id=ids.next("question"),
                answer_ids=[ids.next("answer") for _ in q.answers],
                multichoice_id=ids.next("multichoice"),
                stamp=make_stamp(ids.next("stampseq")),
                timestamp=timestamp,
                userid=ownerid,
            )
            questions_el.append(qel)
    return _serialize(root)


# --------------------------------------------------------------------------- #
# moodle_backup.xml (the manifest)                                            #
# --------------------------------------------------------------------------- #

ROOT_SETTINGS = [
    ("users", "0"), ("anonymize", "0"), ("role_assignments", "0"),
    ("activities", "1"), ("blocks", "1"), ("files", "1"), ("filters", "1"),
    ("comments", "0"), ("badges", "1"), ("calendarevents", "1"),
    ("userscompletion", "0"), ("logs", "0"), ("grade_histories", "0"),
    ("groups", "1"), ("competencies", "1"), ("customfield", "1"),
    ("contentbankcontent", "1"), ("xapistate", "0"), ("legacyfiles", "1"),
]


def build_moodle_backup_xml(
    *, filename: str, courseid: int, course_shortname: str, course_fullname: str,
    course_contextid: int, activities: list[ActivityRef],
    sections: list[SectionRef], timestamp: int,
) -> str:
    root = ET.Element("moodle_backup")
    info = _sub(root, "information")
    _sub(info, "name", filename)
    _sub(info, "moodle_version", "2026042000.02")
    _sub(info, "moodle_release", "5.2+ (Build: 20260501)")
    _sub(info, "backup_version", "2026042000")
    _sub(info, "backup_release", "5.2")
    _sub(info, "backup_date", str(timestamp))
    _sub(info, "mnet_remoteusers", "0")
    _sub(info, "include_files", "1")
    _sub(info, "include_file_references_to_external_content", "0")
    _sub(info, "original_wwwroot", "https://moodle.ims.local")
    _sub(info, "original_site_identifier_hash", uuid.uuid4().hex)
    _sub(info, "original_course_id", str(courseid))
    _sub(info, "original_course_format", "topics")
    _sub(info, "original_course_fullname", course_fullname)
    _sub(info, "original_course_shortname", course_shortname)
    _sub(info, "original_course_startdate", "0")
    _sub(info, "original_course_enddate", "0")
    _sub(info, "original_course_contextid", str(course_contextid))
    _sub(info, "original_system_contextid", "1")

    details = _sub(info, "details")
    detail = ET.SubElement(details, "detail", {"backup_id": uuid.uuid4().hex})
    _sub(detail, "type", "course")
    _sub(detail, "format", "moodle2")
    _sub(detail, "interactive", "1")
    _sub(detail, "mode", "70")
    _sub(detail, "execution", "2")
    _sub(detail, "executiontime", "0")

    contents = _sub(info, "contents")
    acts = _sub(contents, "activities")
    for a in activities:
        ae = _sub(acts, "activity")
        _sub(ae, "moduleid", str(a.cmid))
        _sub(ae, "sectionid", str(a.sectionid))
        _sub(ae, "modulename", a.modulename)
        _sub(ae, "title", a.title)
        _sub(ae, "directory", a.directory)
        _sub(ae, "insubsection", "")
    secs = _sub(contents, "sections")
    for s in sections:
        se = _sub(secs, "section")
        _sub(se, "sectionid", str(s.sectionid))
        _sub(se, "title", s.title)
        _sub(se, "directory", s.directory)
        _sub(se, "parentcmid", "")
        _sub(se, "modname", "")
    course = _sub(contents, "course")
    _sub(course, "courseid", str(courseid))
    _sub(course, "title", course_shortname)
    _sub(course, "directory", "course")

    settings = _sub(info, "settings")
    fn = _sub(settings, "setting")
    _sub(fn, "level", "root")
    _sub(fn, "name", "filename")
    _sub(fn, "value", filename)
    for name, value in ROOT_SETTINGS:
        s = _sub(settings, "setting")
        _sub(s, "level", "root")
        _sub(s, "name", name)
        _sub(s, "value", value)
    for sec in sections:
        for suffix, value in (("included", "1"), ("userinfo", "0")):
            s = _sub(settings, "setting")
            _sub(s, "level", "section")
            _sub(s, "section", f"section_{sec.sectionid}")
            _sub(s, "name", f"section_{sec.sectionid}_{suffix}")
            _sub(s, "value", value)
    for act in activities:
        tag = f"{act.modulename}_{act.cmid}"
        for suffix, value in (("included", "1"), ("userinfo", "0")):
            s = _sub(settings, "setting")
            _sub(s, "level", "activity")
            _sub(s, "activity", tag)
            _sub(s, "name", f"{tag}_{suffix}")
            _sub(s, "value", value)
    return _serialize(root)


def _selftest() -> int:
    ids = IdAllocator()
    q = Question(name="Q1", questiontext="<p>?</p>", generalfeedback="<p>gf</p>",
                 defaultmark=1.0, single=True, shuffleanswers=True,
                 answers=[])
    from quiz_to_backup import Answer  # local import for the selftest
    q.answers = [Answer("<p>a</p>", 1.0, "<p>y</p>"),
                 Answer("<p>b</p>", 0.0, ""),
                 Answer("<p>c</p>", 0.0, ""),
                 Answer("<p>d</p>", 0.0, "")]
    spec = QuizSpec(cmid=12, contextid=102, name="L1 Quiz", questions=[q])
    qx = build_question_bank([spec], ids, timestamp=0)
    ET.fromstring(qx)
    assert spec.top_category_id and spec.default_category_id
    assert len(spec.qbe_ids) == 1

    sec = SectionRef(sectionid=2, number=1, name="Module 1", sequence=[11, 12])
    for content in build_section_files(sec, 0).values():
        ET.fromstring(content)
    for content in build_course_files(courseid=1, contextid=1, shortname="C",
                                      fullname="Course", timestamp=0).values():
        ET.fromstring(content)
    ET.fromstring(build_gradebook_xml(grade_category_id=1, course_item_id=2, timestamp=0))
    mb = build_moodle_backup_xml(
        filename="test.mbz", courseid=1, course_shortname="C", course_fullname="Course",
        course_contextid=1,
        activities=[ActivityRef(11, 2, "page", "Overview"),
                    ActivityRef(12, 2, "quiz", "L1 Quiz")],
        sections=[SectionRef(2, 1, "Module 1", [11, 12])], timestamp=0)
    ET.fromstring(mb)
    assert "section_2_included" in mb and "quiz_12_included" in mb
    print("Self-test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
