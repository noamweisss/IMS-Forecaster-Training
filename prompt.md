I need you to convert a folder of meteorological presentations into a 
complete Moodle learning module. Work through this step by step.

━━ CONTEXT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Course:   Aviation Weather Forecasting Certification — IMS
Module:   1 — based on sources 01-04, name to be determined
Audience: Professional meteorologists at the Israeli Meteorological Service taking a refresh-course on Aviation Weather Forecasting
Format:   Standalone self-paced online course. No instructor. No class. The module IS the learning material.
Output:   All files go in ./module_output/

━━ STEP 1: EXTRACT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Install python-pptx, pymupdf, and python-docx.
Write and run Python to extract all text, titles, bullet points, and
speaker notes from every file in ./source_files/ (PPTX, PDF, and DOCX mixed).
Save the result as ./module_output/_extraction.json

━━ STEP 2: DESIGN MODULE STRUCTURE ━━━━━━━━━━━━━━━━━━━━
Using the extracted content, create ./module_output/module_structure.json:
- Group content into 3–5 coherent lessons
- Each lesson needs: title, 2–3 Bloom's-taxonomy learning objectives,
  key concepts, and specific descriptions of diagrams that would aid understanding
- List module-level competencies (what does completing this module certify?)
- End-of-module quiz plan: 15 questions, 75% pass rate

━━ STEP 3: LESSON PAGES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For each lesson, create ./module_output/lessons/NN_lesson_name.html

The content must be visual-forward. Requirements:
- Open with a styled "By the end of this lesson you will be able to:" box
- Professional prose: 2–4 sentences per paragraph, no filler, no fluff.
  These are experts — respect their time.
- At least 2 INLINE SVG DIAGRAMS per lesson for key concepts (process flows,
  decision trees, system diagrams, annotated sequences). Use viewBox="0 0 680 H",
  flat colors only, dark-mode safe text colors. Make them genuinely explanatory,
  not decorative.
- HTML comparison tables for any reference data or classification systems
- Callout boxes for warnings, key formulas, and important operational notes
- End with a "Key Takeaways" summary box (4–6 bullets)
- Where a real photograph is needed (clouds, instruments, phenomena),
  insert: <div class="image-needed">📷 Needed: [specific description]</div>

Use this CSS (paste into each file's <style> tag):
:root { --bg:#fff; --surface:#f6f5f0; --border:#e2dfd6; --text:#1a1917;
  --muted:#6b6a65; --accent:#185fa5; --accent-light:#e6f1fb;
  --note-bg:#e1f5ee; --note-border:#0F6E56; --warn-bg:#faeeda;
  --warn-border:#BA7517; --key-bg:#EEEDFE; --key-border:#534AB7; }
@media (prefers-color-scheme:dark) { :root { --bg:#1a1917; --surface:#242320;
  --border:#3a3835; --text:#e8e6df; --muted:#9a9890;
  --accent-light:#042c53; --note-bg:#04342c; --warn-bg:#412402; --key-bg:#26215c; } }
body { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  max-width:840px; margin:0 auto; padding:2rem 1.5rem;
  background:var(--bg); color:var(--text); line-height:1.75; font-size:16px; }
h1 { font-size:1.8rem; font-weight:600; }
h2 { font-size:1.25rem; font-weight:600; margin-top:2.5rem;
  padding-bottom:0.4rem; border-bottom:1.5px solid var(--border); }
h3 { font-size:1.05rem; font-weight:600; margin-top:1.75rem; }
p { margin:0.7rem 0; max-width:72ch; }
figure { margin:2rem 0; }
figcaption { font-size:0.85rem; color:var(--muted); margin-top:0.6rem;
  font-style:italic; text-align:center; }
svg { max-width:100%; height:auto; display:block; margin:0 auto; }
table { border-collapse:collapse; width:100%; margin:1.5rem 0; font-size:0.9rem; }
th { background:var(--accent); color:#fff; padding:0.55rem 0.9rem; text-align:left; }
td { padding:0.5rem 0.9rem; border-bottom:1px solid var(--border); }
tr:nth-child(even) td { background:var(--surface); }
.callout { border-radius:8px; padding:1rem 1.25rem; margin:1.5rem 0; }
.callout-note    { background:var(--note-bg);  border-left:4px solid var(--note-border); }
.callout-warning { background:var(--warn-bg);  border-left:4px solid var(--warn-border); }
.callout-key     { background:var(--key-bg);   border-left:4px solid var(--key-border); }
.objectives { background:var(--surface); border-radius:8px; padding:1.25rem 1.5rem; margin:1.5rem 0; }
.lesson-summary { background:var(--accent-light); border-radius:8px;
  padding:1.25rem 1.5rem; margin:2.5rem 0 1rem; }
.image-needed { border:2px dashed var(--border); border-radius:8px; padding:1.5rem;
  margin:1.5rem 0; text-align:center; color:var(--muted); background:var(--surface); }

━━ STEP 4: QUIZ FILES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For each lesson, create ./module_output/lessons/NN_lesson_name_quiz.xml
with 5–6 multiple choice questions in Moodle XML format:
- Application level — scenarios and judgment calls, not pure recall
- 4 plausible options; wrong answers should reflect real expert misconceptions
- Include a rationale explaining why the correct answer is right

Moodle XML format:
<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name><text>Q01 — short label</text></name>
    <questiontext format="html"><text><![CDATA[<p>Question text</p>]]></text></questiontext>
    <generalfeedback format="html"><text><![CDATA[<p>Rationale</p>]]></text></generalfeedback>
    <defaultgrade>1</defaultgrade><single>true</single><shuffleanswers>true</shuffleanswers>
    <answer fraction="100" format="html"><text><![CDATA[<p>Correct option</p>]]></text></answer>
    <answer fraction="0"   format="html"><text><![CDATA[<p>Wrong option</p>]]></text></answer>
    <answer fraction="0"   format="html"><text><![CDATA[<p>Wrong option</p>]]></text></answer>
    <answer fraction="0"   format="html"><text><![CDATA[<p>Wrong option</p>]]></text></answer>
  </question>
</quiz>

Also create ./module_output/module_quiz_all_questions.xml combining all questions.

━━ STEP 5: OVERVIEW + README ━━━━━━━━━━━━━━━━━━━━━━━━━━
- ./module_output/00_module_overview.html — module intro page listing all
  lessons, their objectives, estimated durations, and quiz/pass criteria.
  Same CSS as lesson pages.
- ./module_output/IMAGES_TO_SOURCE.md — list of every 📷 image-needed item
  flagged across all lessons, for human sourcing.
- ./module_output/README.md — step-by-step Moodle import instructions.

━━ GO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Complete all 5 steps in order. After each step confirm what was produced
before moving to the next. Ask me if any source content is ambiguous.