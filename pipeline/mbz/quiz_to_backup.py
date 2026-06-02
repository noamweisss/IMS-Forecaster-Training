#!/usr/bin/env python3
"""
quiz_to_backup.py — Convert a lesson's Moodle *import*-format quiz XML into the
Moodle *backup*-format <question> elements used inside a .mbz's questions.xml.

The two formats are NOT the same:

  import  (lessons/NN_<slug>_quiz.xml, what the agent writes)
      <quiz>
        <question type="multichoice">
          <name><text>T</text></name>
          <questiontext format="html"><text><![CDATA[H]]></text></questiontext>
          <generalfeedback ...><text><![CDATA[H]]></text></generalfeedback>
          <defaultgrade>1</defaultgrade><single>true</single><shuffleanswers>true</shuffleanswers>
          <answer fraction="100" ...><text><![CDATA[A]]></text>
            <feedback ...><text></text></feedback></answer>
          ... x4 ...
        </question>
      </quiz>

  backup  (questions.xml, what a .mbz restore reads)
      <question id="..">
        <name>T</name>
        <questiontext>H</questiontext><questiontextformat>1</questiontextformat>
        ... <qtype>multichoice</qtype> ...
        <plugin_qtype_multichoice_question>
          <answers><answer id=".."><answertext>A</answertext><fraction>1.0000000</fraction>...</answer>...</answers>
          <multichoice id="..">...</multichoice>
        </plugin_qtype_multichoice_question>
        ...
      </question>

See docs/mbz_format.md for the full mapping. This module only handles the
single-question conversion; wrapping questions into categories /
question_bank_entries happens in the questions.xml assembly step.

Run directly for a self-test against module 1:
    python pipeline/mbz/quiz_to_backup.py
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


# Standard multichoice feedback strings, copied verbatim from the reference
# backup (docs/mbz_reference/extracted/questions.xml).
CORRECT_FEEDBACK = "<p>Your answer is correct.</p>"
PARTIAL_FEEDBACK = "<p>Your answer is partially correct.</p>"
INCORRECT_FEEDBACK = "<p>Your answer is incorrect.</p>"

PENALTY = "0.3333333"


@dataclass
class Answer:
    text: str            # HTML
    fraction: float      # 0.0 .. 1.0 (import uses 0..100; we normalise here)
    feedback: str = ""   # HTML


@dataclass
class Question:
    name: str
    questiontext: str            # HTML
    generalfeedback: str         # HTML
    defaultmark: float
    single: bool
    shuffleanswers: bool
    answers: list[Answer] = field(default_factory=list)


def _inner_text(node: ET.Element | None) -> str:
    """Text content of a node (the un-CDATA'd string), or '' if missing/None."""
    if node is None or node.text is None:
        return ""
    return node.text


def _bool(text: str | None, default: bool = True) -> bool:
    if text is None:
        return default
    return text.strip().lower() in ("1", "true", "yes")


def _decimal7(value: float) -> str:
    """Moodle stores fractions/marks with 7 decimal places."""
    return f"{value:.7f}"


def parse_quiz_file(path: Path) -> list[Question]:
    """Parse one import-format *_quiz.xml into a list of Question objects.

    Non-multichoice and `type="category"` entries are skipped (we only author
    multichoice; category markers carry no question content)."""
    root = ET.parse(path).getroot()
    questions: list[Question] = []
    for q in root.findall("question"):
        if q.get("type") != "multichoice":
            continue
        name = _inner_text(q.find("name/text"))
        questiontext = _inner_text(q.find("questiontext/text"))
        generalfeedback = _inner_text(q.find("generalfeedback/text"))
        defaultmark = float(_inner_text(q.find("defaultgrade")) or "1")
        single = _bool(_inner_text(q.find("single")) or None, default=True)
        shuffle = _bool(_inner_text(q.find("shuffleanswers")) or None, default=True)

        answers: list[Answer] = []
        for a in q.findall("answer"):
            frac_pct = float(a.get("fraction", "0"))
            answers.append(
                Answer(
                    text=_inner_text(a.find("text")),
                    fraction=frac_pct / 100.0,
                    feedback=_inner_text(a.find("feedback/text")),
                )
            )
        questions.append(
            Question(
                name=name,
                questiontext=questiontext,
                generalfeedback=generalfeedback,
                defaultmark=defaultmark,
                single=single,
                shuffleanswers=shuffle,
                answers=answers,
            )
        )
    return questions


def _sub(parent: ET.Element, tag: str, text: str | None = None) -> ET.Element:
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = text
    return el


def build_question_element(
    q: Question,
    *,
    question_id: int,
    answer_ids: list[int],
    multichoice_id: int,
    stamp: str,
    timestamp: int,
    userid: int = 2,
) -> ET.Element:
    """Render a single Question as a backup-format <question> element.

    `answer_ids` must have one id per answer in `q.answers`. The element this
    returns is what goes inside a question_versions/<questions> wrapper in
    questions.xml. HTML is stored as element text — ElementTree escapes it
    (the backup format uses escaped entities, not CDATA)."""
    if len(answer_ids) != len(q.answers):
        raise ValueError("answer_ids must align 1:1 with q.answers")

    question = ET.Element("question", {"id": str(question_id)})
    _sub(question, "parent", "0")
    _sub(question, "name", q.name)
    _sub(question, "questiontext", q.questiontext)
    _sub(question, "questiontextformat", "1")
    _sub(question, "generalfeedback", q.generalfeedback)
    _sub(question, "generalfeedbackformat", "1")
    _sub(question, "defaultmark", _decimal7(q.defaultmark))
    _sub(question, "penalty", PENALTY)
    _sub(question, "qtype", "multichoice")
    _sub(question, "length", "1")
    _sub(question, "stamp", stamp)
    _sub(question, "timecreated", str(timestamp))
    _sub(question, "timemodified", str(timestamp))
    _sub(question, "createdby", str(userid))
    _sub(question, "modifiedby", str(userid))

    plugin = _sub(question, "plugin_qtype_multichoice_question")
    answers_el = _sub(plugin, "answers")
    for ans, aid in zip(q.answers, answer_ids):
        a = ET.SubElement(answers_el, "answer", {"id": str(aid)})
        _sub(a, "answertext", ans.text)
        _sub(a, "answerformat", "1")
        _sub(a, "fraction", _decimal7(ans.fraction))
        _sub(a, "feedback", ans.feedback)
        _sub(a, "feedbackformat", "1")

    mc = ET.SubElement(plugin, "multichoice", {"id": str(multichoice_id)})
    _sub(mc, "layout", "0")
    _sub(mc, "single", "1" if q.single else "0")
    _sub(mc, "shuffleanswers", "1" if q.shuffleanswers else "0")
    _sub(mc, "correctfeedback", CORRECT_FEEDBACK)
    _sub(mc, "correctfeedbackformat", "1")
    _sub(mc, "partiallycorrectfeedback", PARTIAL_FEEDBACK)
    _sub(mc, "partiallycorrectfeedbackformat", "1")
    _sub(mc, "incorrectfeedback", INCORRECT_FEEDBACK)
    _sub(mc, "incorrectfeedbackformat", "1")
    _sub(mc, "answernumbering", "abc")
    _sub(mc, "shownumcorrect", "1")
    _sub(mc, "showstandardinstruction", "0")

    # Empty qbank sub-plugin blocks the restore expects to be present.
    comment = _sub(question, "plugin_qbank_comment_question")
    _sub(comment, "comments")
    customfields = _sub(question, "plugin_qbank_customfields_question")
    _sub(customfields, "customfields")
    _sub(question, "question_hints")
    _sub(question, "tags")
    return question


def _selftest() -> int:
    """Parse every module-1 quiz, convert it, and assert basic invariants."""
    repo = Path(__file__).resolve().parents[2]
    lessons = repo / "courses/aviation-weather/module-1/lessons"
    quiz_files = sorted(lessons.glob("*_quiz.xml"))
    if not quiz_files:
        print(f"No quiz files found under {lessons}", file=sys.stderr)
        return 1

    total = 0
    for qf in quiz_files:
        questions = parse_quiz_file(qf)
        assert questions, f"{qf.name}: no questions parsed"
        for i, q in enumerate(questions):
            assert q.name, f"{qf.name} Q{i}: empty name"
            assert q.questiontext, f"{qf.name} Q{i}: empty questiontext"
            assert len(q.answers) == 4, f"{qf.name} Q{i}: expected 4 answers, got {len(q.answers)}"
            correct = [a for a in q.answers if a.fraction > 0.5]
            assert len(correct) == 1, f"{qf.name} Q{i}: expected exactly 1 correct answer"
            # The conversion must produce well-formed XML.
            el = build_question_element(
                q,
                question_id=i + 1,
                answer_ids=[1, 2, 3, 4],
                multichoice_id=i + 1,
                stamp="selftest+0+AAA",
                timestamp=0,
            )
            # Round-trip through serialise+parse to prove well-formedness.
            ET.fromstring(ET.tostring(el, encoding="unicode"))
        total += len(questions)
        print(f"  {qf.name}: {len(questions)} question(s) OK")

    print(f"\nSelf-test passed: {total} questions across {len(quiz_files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
