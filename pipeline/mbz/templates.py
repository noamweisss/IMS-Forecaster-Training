#!/usr/bin/env python3
"""
templates.py — The near-constant boilerplate XML files that appear in every
Moodle 5.2 .mbz, copied verbatim from the reference backup
(docs/mbz_reference/extracted/). Files that need per-backup substitution
(moodle_backup.xml, course.xml, sections, activities, questions.xml,
gradebook.xml) are built in code elsewhere, not here.

Design note: the reference splits these across ~20 tiny files. We keep them as
named string constants in this one module instead — it is far easier to review
and diff a single file than two dozen near-empty XML stubs, and it keeps the
builder self-contained (no reading from docs/ at build time). Each constant is
the *complete* file content including the XML declaration.
"""

from __future__ import annotations

XML_DECL = '<?xml version="1.0" encoding="UTF-8"?>\n'

# --- Per-activity boilerplate (identical for page and quiz) -----------------

ACTIVITY_ROLES = XML_DECL + (
    "<roles>\n"
    "  <role_overrides>\n"
    "  </role_overrides>\n"
    "  <role_assignments>\n"
    "  </role_assignments>\n"
    "</roles>"
)

ACTIVITY_FILTERS = XML_DECL + (
    "<filters>\n"
    "  <filter_actives>\n"
    "  </filter_actives>\n"
    "  <filter_configs>\n"
    "  </filter_configs>\n"
    "</filters>"
)

ACTIVITY_CALENDAR = XML_DECL + "<events>\n</events>"

ACTIVITY_COMPETENCIES = XML_DECL + (
    "<course_module_competencies>\n"
    "  <competencies>\n"
    "  </competencies>\n"
    "</course_module_competencies>"
)

ACTIVITY_GRADE_HISTORY = XML_DECL + (
    "<grade_history>\n"
    "  <grade_grades>\n"
    "  </grade_grades>\n"
    "</grade_history>"
)

# A page has no grade items; its grades.xml is an empty activity_gradebook.
ACTIVITY_GRADES_EMPTY = XML_DECL + (
    "<activity_gradebook>\n"
    "  <grade_items>\n"
    "  </grade_items>\n"
    "  <grade_letters>\n"
    "  </grade_letters>\n"
    "</activity_gradebook>"
)

# A page's inforef.xml is empty (no files, grades, or question categories).
ACTIVITY_INFOREF_EMPTY = XML_DECL + "<inforef>\n</inforef>"

# --- Per-section boilerplate ------------------------------------------------

SECTION_INFOREF_EMPTY = XML_DECL + "<inforef>\n</inforef>"

# --- Course-level boilerplate -----------------------------------------------

COURSE_FILTERS = ACTIVITY_FILTERS

COURSE_CALENDAR = ACTIVITY_CALENDAR

COURSE_ROLES = ACTIVITY_ROLES

COURSE_COMPETENCIES = XML_DECL + (
    "<course_competencies>\n"
    "  <competencies>\n"
    "  </competencies>\n"
    "  <user_competencies>\n"
    "  </user_competencies>\n"
    "</course_competencies>"
)

COURSE_COMPLETIONDEFAULTS = XML_DECL + (
    "<course_completion_defaults>\n</course_completion_defaults>"
)

COURSE_CONTENTBANK = XML_DECL + "<contents>\n</contents>"

# Reference course/inforef.xml references the student role (id 5).
COURSE_INFOREF = XML_DECL + (
    "<inforef>\n"
    "  <roleref>\n"
    "    <role>\n"
    "      <id>5</id>\n"
    "    </role>\n"
    "  </roleref>\n"
    "</inforef>"
)

# Manual/guest/self enrolment methods, no users. roleid 5 = student.
COURSE_ENROLMENTS = XML_DECL + (
    "<enrolments>\n"
    "  <enrols>\n"
    "    <enrol id=\"4\">\n"
    "      <enrol>manual</enrol>\n"
    "      <status>0</status>\n"
    "      <name>$@NULL@$</name>\n"
    "      <enrolperiod>0</enrolperiod>\n"
    "      <enrolstartdate>0</enrolstartdate>\n"
    "      <enrolenddate>0</enrolenddate>\n"
    "      <expirynotify>0</expirynotify>\n"
    "      <expirythreshold>86400</expirythreshold>\n"
    "      <notifyall>0</notifyall>\n"
    "      <password>$@NULL@$</password>\n"
    "      <cost>$@NULL@$</cost>\n"
    "      <currency>$@NULL@$</currency>\n"
    "      <roleid>5</roleid>\n"
    "      <customint1>1</customint1>\n"
    "      <customint2>$@NULL@$</customint2>\n"
    "      <customint3>$@NULL@$</customint3>\n"
    "      <customint4>$@NULL@$</customint4>\n"
    "      <customint5>$@NULL@$</customint5>\n"
    "      <customint6>$@NULL@$</customint6>\n"
    "      <customint7>$@NULL@$</customint7>\n"
    "      <customint8>$@NULL@$</customint8>\n"
    "      <customchar1>$@NULL@$</customchar1>\n"
    "      <customchar2>$@NULL@$</customchar2>\n"
    "      <customchar3>$@NULL@$</customchar3>\n"
    "      <customdec1>$@NULL@$</customdec1>\n"
    "      <customdec2>$@NULL@$</customdec2>\n"
    "      <customtext1>$@NULL@$</customtext1>\n"
    "      <customtext2>$@NULL@$</customtext2>\n"
    "      <customtext3>$@NULL@$</customtext3>\n"
    "      <customtext4>$@NULL@$</customtext4>\n"
    "      <timecreated>0</timecreated>\n"
    "      <timemodified>0</timemodified>\n"
    "      <user_enrolments>\n"
    "      </user_enrolments>\n"
    "    </enrol>\n"
    "    <enrol id=\"5\">\n"
    "      <enrol>guest</enrol>\n"
    "      <status>1</status>\n"
    "      <name>$@NULL@$</name>\n"
    "      <enrolperiod>0</enrolperiod>\n"
    "      <enrolstartdate>0</enrolstartdate>\n"
    "      <enrolenddate>0</enrolenddate>\n"
    "      <expirynotify>0</expirynotify>\n"
    "      <expirythreshold>0</expirythreshold>\n"
    "      <notifyall>0</notifyall>\n"
    "      <password></password>\n"
    "      <cost>$@NULL@$</cost>\n"
    "      <currency>$@NULL@$</currency>\n"
    "      <roleid>0</roleid>\n"
    "      <customint1>$@NULL@$</customint1>\n"
    "      <customint2>$@NULL@$</customint2>\n"
    "      <customint3>$@NULL@$</customint3>\n"
    "      <customint4>$@NULL@$</customint4>\n"
    "      <customint5>$@NULL@$</customint5>\n"
    "      <customint6>$@NULL@$</customint6>\n"
    "      <customint7>$@NULL@$</customint7>\n"
    "      <customint8>$@NULL@$</customint8>\n"
    "      <customchar1>$@NULL@$</customchar1>\n"
    "      <customchar2>$@NULL@$</customchar2>\n"
    "      <customchar3>$@NULL@$</customchar3>\n"
    "      <customdec1>$@NULL@$</customdec1>\n"
    "      <customdec2>$@NULL@$</customdec2>\n"
    "      <customtext1>$@NULL@$</customtext1>\n"
    "      <customtext2>$@NULL@$</customtext2>\n"
    "      <customtext3>$@NULL@$</customtext3>\n"
    "      <customtext4>$@NULL@$</customtext4>\n"
    "      <timecreated>0</timecreated>\n"
    "      <timemodified>0</timemodified>\n"
    "      <user_enrolments>\n"
    "      </user_enrolments>\n"
    "    </enrol>\n"
    "    <enrol id=\"6\">\n"
    "      <enrol>self</enrol>\n"
    "      <status>1</status>\n"
    "      <name>$@NULL@$</name>\n"
    "      <enrolperiod>0</enrolperiod>\n"
    "      <enrolstartdate>0</enrolstartdate>\n"
    "      <enrolenddate>0</enrolenddate>\n"
    "      <expirynotify>0</expirynotify>\n"
    "      <expirythreshold>86400</expirythreshold>\n"
    "      <notifyall>0</notifyall>\n"
    "      <password>$@NULL@$</password>\n"
    "      <cost>$@NULL@$</cost>\n"
    "      <currency>$@NULL@$</currency>\n"
    "      <roleid>5</roleid>\n"
    "      <customint1>0</customint1>\n"
    "      <customint2>0</customint2>\n"
    "      <customint3>0</customint3>\n"
    "      <customint4>1</customint4>\n"
    "      <customint5>0</customint5>\n"
    "      <customint6>1</customint6>\n"
    "      <customint7>$@NULL@$</customint7>\n"
    "      <customint8>$@NULL@$</customint8>\n"
    "      <customchar1>$@NULL@$</customchar1>\n"
    "      <customchar2>$@NULL@$</customchar2>\n"
    "      <customchar3>$@NULL@$</customchar3>\n"
    "      <customdec1>$@NULL@$</customdec1>\n"
    "      <customdec2>$@NULL@$</customdec2>\n"
    "      <customtext1>$@NULL@$</customtext1>\n"
    "      <customtext2>$@NULL@$</customtext2>\n"
    "      <customtext3>$@NULL@$</customtext3>\n"
    "      <customtext4>$@NULL@$</customtext4>\n"
    "      <timecreated>0</timecreated>\n"
    "      <timemodified>0</timemodified>\n"
    "      <user_enrolments>\n"
    "      </user_enrolments>\n"
    "    </enrol>\n"
    "  </enrols>\n"
    "</enrolments>"
)

# --- Top-level boilerplate --------------------------------------------------

TOP_BADGES = XML_DECL + "<badges>\n</badges>"

TOP_COMPLETION = XML_DECL + "<course_completion>\n</course_completion>"

TOP_OUTCOMES = XML_DECL + "<outcomes_definition>\n</outcomes_definition>"

TOP_SCALES = XML_DECL + "<scales_definition>\n</scales_definition>"

TOP_GROUPS = XML_DECL + (
    "<groups>\n"
    "  <groupcustomfields>\n"
    "  </groupcustomfields>\n"
    "  <groupings>\n"
    "    <groupingcustomfields>\n"
    "    </groupingcustomfields>\n"
    "  </groupings>\n"
    "</groups>"
)

TOP_GRADE_HISTORY = ACTIVITY_GRADE_HISTORY

TOP_FILES = XML_DECL + "<files>\n</files>"

TOP_ROLES = XML_DECL + (
    "<roles_definition>\n"
    "  <role id=\"5\">\n"
    "    <name></name>\n"
    "    <shortname>student</shortname>\n"
    "    <nameincourse>$@NULL@$</nameincourse>\n"
    "    <description></description>\n"
    "    <sortorder>5</sortorder>\n"
    "    <archetype>student</archetype>\n"
    "  </role>\n"
    "</roles_definition>"
)

# Files written verbatim into every activity directory, keyed by filename.
ACTIVITY_COMMON_FILES: dict[str, str] = {
    "roles.xml": ACTIVITY_ROLES,
    "filters.xml": ACTIVITY_FILTERS,
    "calendar.xml": ACTIVITY_CALENDAR,
    "competencies.xml": ACTIVITY_COMPETENCIES,
    "grade_history.xml": ACTIVITY_GRADE_HISTORY,
}

# Files written verbatim into the course/ directory, keyed by filename.
COURSE_COMMON_FILES: dict[str, str] = {
    "enrolments.xml": COURSE_ENROLMENTS,
    "roles.xml": COURSE_ROLES,
    "filters.xml": COURSE_FILTERS,
    "calendar.xml": COURSE_CALENDAR,
    "competencies.xml": COURSE_COMPETENCIES,
    "completiondefaults.xml": COURSE_COMPLETIONDEFAULTS,
    "inforef.xml": COURSE_INFOREF,
    "contentbank.xml": COURSE_CONTENTBANK,
}

# Files written verbatim at the archive root, keyed by filename.
TOP_COMMON_FILES: dict[str, str] = {
    "badges.xml": TOP_BADGES,
    "completion.xml": TOP_COMPLETION,
    "outcomes.xml": TOP_OUTCOMES,
    "scales.xml": TOP_SCALES,
    "groups.xml": TOP_GROUPS,
    "grade_history.xml": TOP_GRADE_HISTORY,
    "files.xml": TOP_FILES,
    "roles.xml": TOP_ROLES,
}
