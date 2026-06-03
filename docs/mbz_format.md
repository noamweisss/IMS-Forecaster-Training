# Moodle `.mbz` Format — Schema Map (Moodle 5.2)

This is the canonical reference for `pipeline/build_mbz.py`. It documents the
Moodle backup (`.mbz`) structure we target, derived from a real backup exported
from the IMS Moodle instance. The raw reference lives in
[`mbz_reference/`](mbz_reference/) — the original `.mbz` plus its fully
extracted XML tree. When in doubt, read the reference files directly; they are
ground truth.

> **History.** A `.mbz` builder was deferred on 2026-05-19 (see
> [journal.md](journal.md)) because the target Moodle version and schema were
> unknown. The owner then exported a throwaway course as a reference backup,
> which unblocked the work. This doc captures what that reference taught us.

## Target version (stamp these exactly)

| Field | Value |
|-------|-------|
| `moodle_version` | `2026042000.02` |
| `moodle_release` | `5.2+ (Build: 20260501)` |
| `backup_version` | `2026042000` |
| `backup_release` | `5.2` |
| backup `type` / `format` | `course` / `moodle2` |
| `<module version=...>` (every activity) | `2026042000` |

A `.mbz` is just a **gzipped tar** of the tree below (the file extension is
`.mbz`, the contents are `.tar.gz`).

## Archive layout

```
.ARCHIVE_INDEX            ← plaintext index of every entry (REQUIRED, 4.3+/5.x)
moodle_backup.xml         ← the manifest: activities, sections, course, settings
course/
  course.xml              ← course record (shortname, fullname, format=topics, ...)
  enrolments.xml roles.xml filters.xml calendar.xml competencies.xml
  completiondefaults.xml inforef.xml contentbank.xml
sections/
  section_<id>/section.xml   ← one per section; <sequence> orders cmids
  section_<id>/inforef.xml
activities/
  page_<cmid>/  module.xml page.xml + boilerplate
  quiz_<cmid>/  module.xml quiz.xml inforef.xml grades.xml + boilerplate
questions.xml             ← the whole question bank (all categories)
gradebook.xml             ← course grade_category + course grade_item
files.xml                 ← file pool (EMPTY for us — images are base64 inline)
badges.xml completion.xml outcomes.xml scales.xml groups.xml roles.xml
grade_history.xml
moodle_backup.log         ← can be empty
```

We only generate **Page** and **Quiz** activities. The reference also contained a
default `forum` (Announcements) and a `qbank` activity — we deliberately omit
both; a restore does not require them.

### `.ARCHIVE_INDEX`

First line: `Moodle archive file index. Count: <N>` where N is the number of
entries that follow. Then one line per entry, tab-separated:

```
<path>\t<type>\t<size>\t<mtime>
```
- `type` is `d` for a directory (size `0`, mtime `?`) or `f` for a file.
- `<size>` is the byte size of the file; `<mtime>` a unix timestamp.
- Directories are listed before their contents. `moodle_backup.log` is listed
  last. The index does **not** list itself.

## `moodle_backup.xml` (the manifest)

`<information>` carries the version stamps above plus:
- `<details>` — one `<detail>` with a random hex `backup_id`, `type=course`,
  `format=moodle2`, `mode=70`, `interactive=1`, `execution=2`.
- `<contents>`:
  - `<activities>` — one `<activity>` per cmid: `moduleid` (cmid), `sectionid`,
    `modulename` (`page`/`quiz`), `title`, `directory`
    (`activities/page_<cmid>`), empty `insubsection`.
  - `<sections>` — one `<section>` per section: `sectionid`, `title` (the
    section *number* as a string, e.g. `0`, or the section name), `directory`,
    empty `parentcmid`/`modname`.
  - `<course>` — `courseid`, `title` (shortname), `directory=course`.
- `<settings>` — root-level flags (`users=0`, `role_assignments=0`,
  `activities=1`, `files=1`, ...), then per-section and per-activity
  `<setting>` blocks of the form `<level>section|activity</level>` +
  `<name>section_<id>_included</name>` + `<value>1</value>` and a matching
  `_userinfo=0`. **Every section and activity must have its included/userinfo
  pair**, or the restore UI won't show it.

## Sections

`sections/section_<id>/section.xml`:
```xml
<section id="<sectionid>">
  <number>0</number>                 <!-- 0 = General; 1,2,... = topics -->
  <name>$@NULL@$</name>              <!-- or a real name -->
  <summary></summary><summaryformat>1</summaryformat>
  <sequence>7,10</sequence>         <!-- cmids in display order -->
  <visible>1</visible>
  <availabilityjson>$@NULL@$</availabilityjson>
  <component>$@NULL@$</component><itemid>$@NULL@$</itemid>
  <timemodified>...</timemodified>
</section>
```
`<sequence>` is the comma-separated list of cmids shown in that section, in
order. Our module section lists: `overview_page_cmid, L1_page_cmid,
L1_quiz_cmid, L2_page_cmid, L2_quiz_cmid, ...`. `inforef.xml` is empty for
sections with no files/grades.

## Activity: module.xml (the course-module record)

Common to page and quiz; the `id` attribute is the cmid:
```xml
<module id="<cmid>" version="2026042000">
  <modulename>page|quiz</modulename>
  <sectionid><sectionid></sectionid>
  <sectionnumber><n></sectionnumber>
  <idnumber></idnumber><added><ts></added>
  <score>0</score><indent>0</indent>
  <visible>1</visible><visibleoncoursepage>1</visibleoncoursepage><visibleold>1</visibleold>
  <groupmode>0</groupmode><groupingid>0</groupingid>
  <completion>0</completion>           <!-- page=0 (untracked); quiz=2 (automatic), see below -->
  <completiongradeitemnumber>$@NULL@$</completiongradeitemnumber>
  <completionpassgrade>0</completionpassgrade><completionview>0</completionview>
  <completionexpected>0</completionexpected><availability>$@NULL@$</availability>
  <showdescription>0</showdescription><downloadcontent>1</downloadcontent>
  <lang></lang>
  <enableaitools>$@NULL@$</enableaitools><enabledaiactions>$@NULL@$</enabledaiactions>
  <tags></tags>
</module>
```

### Page activity — `page.xml`

```xml
<activity id="<id>" moduleid="<cmid>" modulename="page" contextid="<ctx>">
  <page id="<id>">
    <name>...</name>
    <intro>&lt;p&gt;...&lt;/p&gt;</intro><introformat>1</introformat>
    <content><!-- the lesson body fragment, HTML-ESCAPED --></content>
    <contentformat>1</contentformat>
    <legacyfiles>0</legacyfiles><legacyfileslast>$@NULL@$</legacyfileslast>
    <display>5</display>
    <displayoptions>a:2:{s:10:"printintro";s:1:"0";s:17:"printlastmodified";s:1:"1";}</displayoptions>
    <revision>1</revision><timemodified><ts></timemodified>
  </page>
</activity>
```
The lesson HTML goes in `<content>`, **escaped** (`&lt;p&gt;…`). ElementTree
escapes automatically when you set `.text`. Base64 `data:` image URIs survive
inside the content verbatim — this is why we don't need `files.xml`.

### Quiz completion + grade visibility (V2)

Quizzes are **completion-tracked but ungraded** (roadmap.md). The builder sets:

- `module.xml`: `<completion>2</completion>` (automatic). The other
  `completion*` fields stay at the defaults above — grade is *not* used for
  completion (`completiongradeitemnumber` NULL, `completionpassgrade` 0).
- `quiz.xml`: `<completionminattempts>1</completionminattempts>` — Moodle marks
  the quiz complete once the learner submits one attempt. Also
  `<reviewmaxmarks>0</reviewmaxmarks>` and `<reviewmarks>0</reviewmarks>` so the
  learner never sees a numeric score (other review options — correctness,
  per-answer + general feedback, right answer — stay on).
- `grades.xml`: the quiz grade_item is `<hidden>1</hidden>` — the score stays in
  the gradebook for the instructor but is hidden from the learner.

Net effect: instructors get a completion report showing who finished every
quiz; learners get full feedback but no grade. Pages keep `<completion>0</completion>`.

### Quiz activity — `quiz.xml`

Key fields (full example in the reference): `name`, `intro`,
`preferredbehaviour=deferredfeedback`, `grademethod=1`, `grade=...`, `sumgrades=...`,
plus `<question_instances>` and `<sections>`. The modern (4.x/5.x) link from a
quiz to its questions is by **question bank entry**, not question id:
```xml
<question_instances>
  <question_instance id="<n>">
    <quizid>1</quizid><slot>1</slot><page>1</page>
    <displaynumber>$@NULL@$</displaynumber><requireprevious>0</requireprevious>
    <maxmark>1.0000000</maxmark><quizgradeitemid>$@NULL@$</quizgradeitemid>
    <question_reference id="<n>">
      <usingcontextid><quiz contextid></usingcontextid>
      <component>mod_quiz</component><questionarea>slot</questionarea>
      <questionbankentryid><qbe id></questionbankentryid>
      <version>$@NULL@$</version>
    </question_reference>
  </question_instance>
  ...one per question...
</question_instances>
<sections><section id="1"><firstslot>1</firstslot><heading></heading><shufflequestions>0</shufflequestions></section></sections>
<feedbacks><feedback id="..."><feedbacktext></feedbacktext><feedbacktextformat>1</feedbacktextformat><mingrade>0</mingrade><maxgrade>...</maxgrade></feedback></feedbacks>
```
The quiz's `contextid` must match the `contextid` of its question categories in
`questions.xml` and the grade-item / question-category ids in its `inforef.xml`.

### Activity boilerplate (near-constant)

Per activity dir, beyond `module.xml` + the page/quiz file:
- `roles.xml` — empty `<role_overrides>`/`<role_assignments>`.
- `filters.xml` — empty `<filter_actives>`/`<filter_configs>`.
- `calendar.xml` — empty `<events>`.
- `competencies.xml` — empty `<course_module_competencies>`.
- `grade_history.xml` — empty `<grade_history>`.
- `grades.xml` — `<activity_gradebook>`: **empty** for a page; for a quiz it
  holds the activity's `grade_item` (`itemtype=mod`, `itemmodule=quiz`,
  `iteminstance=<quizid>`, `categoryid=<course grade_category id>`,
  `grademax=...`).
- `inforef.xml` — **page:** empty. **quiz:** references its grade_item id and
  its two question_category ids:
  ```xml
  <inforef>
    <grade_itemref><grade_item><id>3</id></grade_item></grade_itemref>
    <question_categoryref><question_category><id>5</id></question_category>
      <question_category><id>6</id></question_category></question_categoryref>
  </inforef>
  ```

## Question bank — `questions.xml`

One top-level `<question_categories>`. For each quiz we emit a **pair** of
categories scoped to that quiz's `contextid` (`contextlevel=70`,
`contextinstanceid=<cmid>`):
1. `top` (parent `0`, sortorder `0`).
2. `Default for <quiz name>` (parent = the `top` id, sortorder `999`) — holds the
   questions.

Each question is a `question_bank_entry` → `question_version` →
`question_versions` (one `<question_versions version="1" status="ready">`) →
`questions` → `<question>`:
```xml
<question id="<n>">
  <parent>0</parent>
  <name>...</name>
  <questiontext>...HTML...</questiontext><questiontextformat>1</questiontextformat>
  <generalfeedback>...</generalfeedback><generalfeedbackformat>1</generalfeedbackformat>
  <defaultmark>1.0000000</defaultmark><penalty>0.3333333</penalty>
  <qtype>multichoice</qtype><length>1</length>
  <stamp>...</stamp><timecreated>..</timecreated><timemodified>..</timemodified>
  <createdby>2</createdby><modifiedby>2</modifiedby>
  <plugin_qtype_multichoice_question>
    <answers>
      <answer id="<n>">
        <answertext>...HTML...</answertext><answerformat>1</answerformat>
        <fraction>1.0000000</fraction>          <!-- correct; 0.0000000 otherwise -->
        <feedback>...</feedback><feedbackformat>1</feedbackformat>
      </answer>
      ...4 answers...
    </answers>
    <multichoice id="<n>">
      <layout>0</layout><single>1</single><shuffleanswers>1</shuffleanswers>
      <correctfeedback>&lt;p&gt;Your answer is correct.&lt;/p&gt;</correctfeedback><correctfeedbackformat>1</correctfeedbackformat>
      <partiallycorrectfeedback>...</partiallycorrectfeedback><partiallycorrectfeedbackformat>1</partiallycorrectfeedbackformat>
      <incorrectfeedback>...</incorrectfeedback><incorrectfeedbackformat>1</incorrectfeedbackformat>
      <answernumbering>abc</answernumbering><shownumcorrect>1</shownumcorrect><showstandardinstruction>0</showstandardinstruction>
    </multichoice>
  </plugin_qtype_multichoice_question>
  <plugin_qbank_comment_question><comments></comments></plugin_qbank_comment_question>
  <plugin_qbank_customfields_question><customfields></customfields></plugin_qbank_customfields_question>
  <question_hints></question_hints>
  <tags></tags>
</question>
```
`question_bank_entry` carries `questioncategoryid`, `idnumber=$@NULL@$`,
`ownerid`, `nextversion=2`.

### Mapping from our import-format quiz XML

Our `lessons/NN_<slug>_quiz.xml` is Moodle **import** format, which differs from
the **backup** format above. The conversion (`pipeline/mbz/quiz_to_backup.py`):

| Import (`*_quiz.xml`) | Backup (`questions.xml`) |
|---|---|
| `<question type="multichoice">` | `<qtype>multichoice</qtype>` |
| `<name><text>T</text></name>` | `<name>T</name>` |
| `<questiontext format="html"><text><![CDATA[H]]></text>` | `<questiontext>H</questiontext>` + `<questiontextformat>1` |
| `<generalfeedback>…` | `<generalfeedback>` + `<generalfeedbackformat>1` |
| `<defaultgrade>1` | `<defaultmark>1.0000000` |
| `<single>true`, `<shuffleanswers>true` | `<multichoice><single>1`, `<shuffleanswers>1` |
| `<answer fraction="100">…<text>A` | `<answer><fraction>1.0000000</fraction><answertext>A` |
| `<answer fraction="0">` | `<fraction>0.0000000</fraction>` |
| per-answer `<feedback><text>F` | `<feedback>F</feedback>` + `<feedbackformat>1` |

The import format stores HTML in CDATA; the backup format stores it escaped.

## `gradebook.xml` (course level)

A `grade_category` (the course total, `aggregation=13`, `depth=1`, `path=/<id>/`)
and a course `grade_item` (`itemtype=course`). Each quiz's own grade_item lives
in that quiz's `activities/quiz_<cmid>/grades.xml` (not here), with
`categoryid` pointing at this course grade_category.

## ID scheme

Moodle remaps every id on restore, so ids only need to be **internally
consistent and unique within the backup**. `pipeline/mbz/ids.py` uses separate
incrementing counters per entity type (contextid, cmid, sectionid, questionid,
answerid, questionbankentryid, questionversionid, categoryid, gradeitemid). The
one invariant that matters:

> a quiz activity's `contextid` == the `contextid` of its question categories
> == the contexts referenced in its `inforef.xml`.

Using deterministic counters also makes the output byte-stable across runs, so
regenerating a `.mbz` produces clean diffs.

## `$@NULL@$`

Moodle's backup sentinel for a database `NULL`. Emit the literal string
`$@NULL@$` (not an empty element) wherever the reference shows it.
