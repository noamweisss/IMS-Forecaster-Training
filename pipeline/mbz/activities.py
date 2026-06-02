#!/usr/bin/env python3
"""
activities.py — Build the contents of a single activity directory inside a .mbz:
either activities/page_<cmid>/ or activities/quiz_<cmid>/.

Each builder returns a dict mapping the file's path *relative to the archive
root* to its string content. The structure assembler (structure.py) merges these
into the full archive and is responsible for allocating the ids passed in here
and for keeping the quiz↔questions contextid invariant (see docs/mbz_format.md).

All XML is produced with xml.etree.ElementTree; HTML in <content>/<intro> is
stored as element text and therefore escaped automatically (the backup format
uses escaped entities, not CDATA).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass

try:
    from . import templates as T
except ImportError:  # run directly as a script (python pipeline/mbz/activities.py)
    import templates as T


def _serialize(root: ET.Element) -> str:
    ET.indent(root, space="  ")
    return T.XML_DECL + ET.tostring(root, encoding="unicode")


def _sub(parent: ET.Element, tag: str, text: str | None = None) -> ET.Element:
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = text
    return el


def build_module_xml(
    *,
    cmid: int,
    modulename: str,
    sectionid: int,
    sectionnumber: int,
    added_ts: int,
    completion: int = 0,
) -> str:
    """The course-module record shared by page and quiz."""
    m = ET.Element("module", {"id": str(cmid), "version": "2026042000"})
    _sub(m, "modulename", modulename)
    _sub(m, "sectionid", str(sectionid))
    _sub(m, "sectionnumber", str(sectionnumber))
    _sub(m, "idnumber", "")
    _sub(m, "added", str(added_ts))
    _sub(m, "score", "0")
    _sub(m, "indent", "0")
    _sub(m, "visible", "1")
    _sub(m, "visibleoncoursepage", "1")
    _sub(m, "visibleold", "1")
    _sub(m, "groupmode", "0")
    _sub(m, "groupingid", "0")
    _sub(m, "completion", str(completion))
    _sub(m, "completiongradeitemnumber", "$@NULL@$")
    _sub(m, "completionpassgrade", "0")
    _sub(m, "completionview", "0")
    _sub(m, "completionexpected", "0")
    _sub(m, "availability", "$@NULL@$")
    _sub(m, "showdescription", "0")
    _sub(m, "downloadcontent", "1")
    _sub(m, "lang", "")
    _sub(m, "enableaitools", "$@NULL@$")
    _sub(m, "enabledaiactions", "$@NULL@$")
    _sub(m, "tags")
    return _serialize(m)


def _common_activity_files(prefix: str) -> dict[str, str]:
    """roles/filters/calendar/competencies/grade_history for an activity dir."""
    return {f"{prefix}/{name}": content for name, content in T.ACTIVITY_COMMON_FILES.items()}


# --------------------------------------------------------------------------- #
# Page                                                                         #
# --------------------------------------------------------------------------- #

PAGE_DISPLAYOPTIONS = (
    'a:2:{s:10:"printintro";s:1:"0";s:17:"printlastmodified";s:1:"1";}'
)


def build_page_activity(
    *,
    cmid: int,
    instance_id: int,
    contextid: int,
    sectionid: int,
    sectionnumber: int,
    name: str,
    content_html: str,
    timestamp: int,
    intro_html: str = "",
) -> dict[str, str]:
    prefix = f"activities/page_{cmid}"
    files = _common_activity_files(prefix)

    files[f"{prefix}/module.xml"] = build_module_xml(
        cmid=cmid, modulename="page", sectionid=sectionid,
        sectionnumber=sectionnumber, added_ts=timestamp,
    )

    activity = ET.Element(
        "activity",
        {"id": str(instance_id), "moduleid": str(cmid),
         "modulename": "page", "contextid": str(contextid)},
    )
    page = ET.SubElement(activity, "page", {"id": str(instance_id)})
    _sub(page, "name", name)
    _sub(page, "intro", intro_html)
    _sub(page, "introformat", "1")
    _sub(page, "content", content_html)
    _sub(page, "contentformat", "1")
    _sub(page, "legacyfiles", "0")
    _sub(page, "legacyfileslast", "$@NULL@$")
    _sub(page, "display", "5")
    _sub(page, "displayoptions", PAGE_DISPLAYOPTIONS)
    _sub(page, "revision", "1")
    _sub(page, "timemodified", str(timestamp))
    files[f"{prefix}/page.xml"] = _serialize(activity)

    files[f"{prefix}/grades.xml"] = T.ACTIVITY_GRADES_EMPTY
    files[f"{prefix}/inforef.xml"] = T.ACTIVITY_INFOREF_EMPTY
    return files


# --------------------------------------------------------------------------- #
# Quiz                                                                         #
# --------------------------------------------------------------------------- #

@dataclass
class QuestionInstance:
    instance_id: int
    reference_id: int
    slot: int
    qbe_id: int           # question_bank_entry id this slot points at
    maxmark: float = 1.0


def build_quiz_activity(
    *,
    cmid: int,
    instance_id: int,
    contextid: int,
    sectionid: int,
    sectionnumber: int,
    name: str,
    intro_html: str,
    timestamp: int,
    question_instances: list[QuestionInstance],
    grade_item_id: int,
    grade_category_id: int,
    feedback_id: int,
    quiz_section_id: int,
    question_category_ids: list[int],
    grademax: float,
) -> dict[str, str]:
    prefix = f"activities/quiz_{cmid}"
    files = _common_activity_files(prefix)

    # completion=2 = automatic tracking. Combined with completionminattempts=1
    # below, Moodle marks the quiz complete once the learner submits one
    # attempt — our "who did the course" signal — without requiring a passing
    # grade (completiongradeitemnumber stays NULL, completionpassgrade stays 0).
    # See roadmap.md (V2) and the reference quiz_9/module.xml.
    files[f"{prefix}/module.xml"] = build_module_xml(
        cmid=cmid, modulename="quiz", sectionid=sectionid,
        sectionnumber=sectionnumber, added_ts=timestamp, completion=2,
    )

    activity = ET.Element(
        "activity",
        {"id": str(instance_id), "moduleid": str(cmid),
         "modulename": "quiz", "contextid": str(contextid)},
    )
    quiz = ET.SubElement(activity, "quiz", {"id": str(instance_id)})
    _sub(quiz, "name", name)
    _sub(quiz, "intro", intro_html)
    _sub(quiz, "introformat", "1")
    _sub(quiz, "timeopen", "0")
    _sub(quiz, "timeclose", "0")
    _sub(quiz, "timelimit", "0")
    _sub(quiz, "overduehandling", "autosubmit")
    _sub(quiz, "graceperiod", "0")
    _sub(quiz, "preferredbehaviour", "deferredfeedback")
    _sub(quiz, "canredoquestions", "0")
    _sub(quiz, "attempts_number", "0")
    _sub(quiz, "attemptonlast", "0")
    _sub(quiz, "grademethod", "1")
    _sub(quiz, "decimalpoints", "2")
    _sub(quiz, "questiondecimalpoints", "-1")
    # Review-option bitmasks. 0 = never show; 4352/69888 = show at the various
    # review times. We zero the two *marks* options so learners never see a
    # numeric score (these quizzes are completion-tracked, not graded — see
    # roadmap.md V2). Correctness, per-answer feedback, the right answer, and
    # general feedback stay on so the quiz is still a useful self-check.
    _sub(quiz, "reviewattempt", "69888")
    _sub(quiz, "reviewcorrectness", "4352")
    _sub(quiz, "reviewmaxmarks", "0")
    _sub(quiz, "reviewmarks", "0")
    _sub(quiz, "reviewspecificfeedback", "4352")
    _sub(quiz, "reviewgeneralfeedback", "4352")
    _sub(quiz, "reviewrightanswer", "4352")
    _sub(quiz, "reviewoverallfeedback", "4352")
    _sub(quiz, "questionsperpage", "1")
    _sub(quiz, "navmethod", "free")
    _sub(quiz, "shuffleanswers", "1")
    _sub(quiz, "sumgrades", f"{grademax:.5f}")
    _sub(quiz, "grade", f"{grademax:.5f}")
    _sub(quiz, "timecreated", str(timestamp))
    _sub(quiz, "timemodified", str(timestamp))
    _sub(quiz, "password", "")
    _sub(quiz, "subnet", "")
    _sub(quiz, "browsersecurity", "-")
    _sub(quiz, "delay1", "0")
    _sub(quiz, "delay2", "0")
    _sub(quiz, "showuserpicture", "0")
    _sub(quiz, "showblocks", "0")
    _sub(quiz, "completionattemptsexhausted", "0")
    _sub(quiz, "completionminattempts", "1")  # complete after one submitted attempt
    _sub(quiz, "allowofflineattempts", "0")
    _sub(quiz, "precreateattempts", "$@NULL@$")
    _sub(quiz, "subplugin_quizaccess_seb_quiz")
    _sub(quiz, "quiz_grade_items")

    qis = _sub(quiz, "question_instances")
    for qi in question_instances:
        inst = ET.SubElement(qis, "question_instance", {"id": str(qi.instance_id)})
        _sub(inst, "quizid", str(instance_id))
        _sub(inst, "slot", str(qi.slot))
        _sub(inst, "page", str(qi.slot))
        _sub(inst, "displaynumber", "$@NULL@$")
        _sub(inst, "requireprevious", "0")
        _sub(inst, "maxmark", f"{qi.maxmark:.7f}")
        _sub(inst, "quizgradeitemid", "$@NULL@$")
        ref = ET.SubElement(inst, "question_reference", {"id": str(qi.reference_id)})
        _sub(ref, "usingcontextid", str(contextid))
        _sub(ref, "component", "mod_quiz")
        _sub(ref, "questionarea", "slot")
        _sub(ref, "questionbankentryid", str(qi.qbe_id))
        _sub(ref, "version", "$@NULL@$")

    sections = _sub(quiz, "sections")
    sec = ET.SubElement(sections, "section", {"id": str(quiz_section_id)})
    _sub(sec, "firstslot", "1")
    _sub(sec, "heading", "")
    _sub(sec, "shufflequestions", "0")

    feedbacks = _sub(quiz, "feedbacks")
    fb = ET.SubElement(feedbacks, "feedback", {"id": str(feedback_id)})
    _sub(fb, "feedbacktext", "")
    _sub(fb, "feedbacktextformat", "1")
    _sub(fb, "mingrade", "0.00000")
    _sub(fb, "maxgrade", f"{grademax + 1:.5f}")

    _sub(quiz, "overrides")
    _sub(quiz, "grades")
    _sub(quiz, "attempts")
    files[f"{prefix}/quiz.xml"] = _serialize(activity)

    # The quiz's own grade item (activity-level gradebook).
    files[f"{prefix}/grades.xml"] = _build_quiz_grades(
        grade_item_id=grade_item_id, name=name, quiz_instance_id=instance_id,
        category_id=grade_category_id, grademax=grademax, timestamp=timestamp,
    )

    # inforef ties this quiz to its grade item and question categories.
    inforef = ET.Element("inforef")
    gref = _sub(inforef, "grade_itemref")
    gi = _sub(gref, "grade_item")
    _sub(gi, "id", str(grade_item_id))
    qcref = _sub(inforef, "question_categoryref")
    for cat_id in question_category_ids:
        qc = _sub(qcref, "question_category")
        _sub(qc, "id", str(cat_id))
    files[f"{prefix}/inforef.xml"] = _serialize(inforef)
    return files


def _build_quiz_grades(
    *, grade_item_id: int, name: str, quiz_instance_id: int,
    category_id: int, grademax: float, timestamp: int,
) -> str:
    root = ET.Element("activity_gradebook")
    items = _sub(root, "grade_items")
    gi = ET.SubElement(items, "grade_item", {"id": str(grade_item_id)})
    _sub(gi, "categoryid", str(category_id))
    _sub(gi, "itemname", name)
    _sub(gi, "itemtype", "mod")
    _sub(gi, "itemmodule", "quiz")
    _sub(gi, "iteminstance", str(quiz_instance_id))
    _sub(gi, "itemnumber", "0")
    _sub(gi, "iteminfo", "$@NULL@$")
    _sub(gi, "idnumber", "")
    _sub(gi, "calculation", "$@NULL@$")
    _sub(gi, "gradetype", "1")
    _sub(gi, "grademax", f"{grademax:.5f}")
    _sub(gi, "grademin", "0.00000")
    _sub(gi, "scaleid", "$@NULL@$")
    _sub(gi, "outcomeid", "$@NULL@$")
    _sub(gi, "gradepass", "0.00000")
    _sub(gi, "multfactor", "1.00000")
    _sub(gi, "plusfactor", "0.00000")
    _sub(gi, "aggregationcoef", "0.00000")
    _sub(gi, "aggregationcoef2", "1.00000")
    _sub(gi, "weightoverride", "0")
    _sub(gi, "sortorder", str(grade_item_id))
    _sub(gi, "display", "0")
    _sub(gi, "decimals", "$@NULL@$")
    # hidden=1: the score stays in the gradebook for the instructor but is not
    # shown to the learner — these quizzes track completion, not a grade
    # (roadmap.md V2).
    _sub(gi, "hidden", "1")
    _sub(gi, "locked", "0")
    _sub(gi, "locktime", "0")
    _sub(gi, "needsupdate", "0")
    _sub(gi, "timecreated", str(timestamp))
    _sub(gi, "timemodified", str(timestamp))
    _sub(gi, "grade_grades")
    _sub(root, "grade_letters")
    return _serialize(root)


def _selftest() -> int:
    page = build_page_activity(
        cmid=11, instance_id=1, contextid=101, sectionid=2, sectionnumber=1,
        name="Overview", content_html="<p>Hello <b>world</b></p>", timestamp=0,
    )
    quiz = build_quiz_activity(
        cmid=12, instance_id=1, contextid=102, sectionid=2, sectionnumber=1,
        name="L1 Quiz", intro_html="<p>quiz</p>", timestamp=0,
        question_instances=[QuestionInstance(instance_id=1, reference_id=1, slot=1, qbe_id=1)],
        grade_item_id=3, grade_category_id=2, feedback_id=1, quiz_section_id=1,
        question_category_ids=[5, 6], grademax=4.0,
    )
    for label, files in (("page", page), ("quiz", quiz)):
        for path, content in files.items():
            ET.fromstring(content)  # well-formedness
        print(f"  {label}: {len(files)} files OK")
    # invariant: quiz inforef + question_reference both use the quiz contextid
    assert "<usingcontextid>102</usingcontextid>" in quiz["activities/quiz_12/quiz.xml"]
    print("Self-test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
