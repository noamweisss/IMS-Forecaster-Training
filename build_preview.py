import os
import re
import json
import base64
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path("module_output")
LESSONS_DIR = BASE / "lessons"
IMAGES_DIR = LESSONS_DIR / "images"
OUTPUT = BASE / "preview"
OUTPUT.mkdir(exist_ok=True)
(OUTPUT / "images").mkdir(exist_ok=True)

# Copy images
for img in IMAGES_DIR.iterdir():
    if img.is_file():
        import shutil
        shutil.copy2(img, OUTPUT / "images" / img.name)

# Read lesson HTML bodies (strip <html>, <head>, <body> wrappers — keep inner body only)
def extract_body(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    # Extract everything between <body> and </body>
    m = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
    if m:
        return m.group(1).strip()
    return html

lessons_body = {}
lesson_files = sorted([f for f in LESSONS_DIR.iterdir() if f.suffix == '.html' and not f.name.startswith('00')])
for lf in lesson_files:
    lessons_body[lf.stem] = extract_body(lf)

# Parse quiz XML files
def parse_quiz_xml(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()
    questions = []
    for q in root.findall('question'):
        name_el = q.find('name/text')
        name = name_el.text if name_el is not None else ''
        
        qt_el = q.find('questiontext/text')
        qtext = qt_el.text if qt_el is not None else ''
        # Strip CDATA wrapper residue
        qtext = re.sub(r'<!\[CDATA\[', '', qtext)
        qtext = re.sub(r'\]\]>', '', qtext)
        
        fb_el = q.find('generalfeedback/text')
        feedback = fb_el.text if fb_el is not None else ''
        feedback = re.sub(r'<!\[CDATA\[', '', feedback)
        feedback = re.sub(r'\]\]>', '', feedback)
        
        answers = []
        for a in q.findall('answer'):
            frac = a.get('fraction', '0')
            a_text = a.find('text').text if a.find('text') is not None else ''
            a_text = re.sub(r'<!\[CDATA\[', '', a_text)
            a_text = re.sub(r'\]\]>', '', a_text)
            answers.append({'text': a_text, 'correct': frac == '100'})
        
        questions.append({
            'name': name,
            'question': qtext,
            'feedback': feedback,
            'answers': answers
        })
    return questions

quizzes = {}
quiz_files = sorted([f for f in LESSONS_DIR.iterdir() if f.name.endswith('_quiz.xml')])
for qf in quiz_files:
    key = qf.stem.replace('_quiz', '')
    quizzes[key] = parse_quiz_xml(qf)

# Build quiz JSON for embedding
quiz_json = json.dumps(quizzes, ensure_ascii=False)

# Lesson metadata
lesson_meta = [
    {"id": "01_international_regulatory_frameworks", "num": 1, "title": "International Regulatory Frameworks (WMO & ICAO)", "duration": "25 min"},
    {"id": "02_aviation_route_planning_and_fuel_management", "num": 2, "title": "Aviation Route Planning & Fuel Management", "duration": "30 min"},
    {"id": "03_airspace_structure_and_classification", "num": 3, "title": "Airspace Structure & Classification", "duration": "20 min"},
    {"id": "04_principles_of_aviation_altimetry", "num": 4, "title": "Principles of Aviation Altimetry", "duration": "25 min"},
]

# Future modules
future_modules = [
    {"num": 2, "title": "In-flight Aviation Hazards", "topics": "Turbulence, Icing, CB Clouds, Wind Shear, Volcanic Ash"},
    {"num": 3, "title": "Terminal Area Hazards & Visibility", "topics": "Fog, Haze, Cloud Base & Top Forecasting"},
    {"num": 4, "title": "Aviation Forecast Products & Warnings", "topics": "Area & Aerodrome Warnings, TAF Writing, Tropical Storms, WAFC Maps"},
]

# Build the HTML
lesson_sections = ""
for lm in lesson_meta:
    body = lessons_body.get(lm["id"], "")
    # Fix image paths for preview folder structure (images/ stays the same)
    lesson_sections += f'<div class="lesson-page" id="lesson-{lm["num"]}" style="display:none;">\n{body}\n</div>\n\n'

# Quiz sections built via JS, but we need containers
quiz_containers = ""
for lm in lesson_meta:
    quiz_containers += f'<div class="lesson-page quiz-page" id="quiz-{lm["num"]}" style="display:none;"></div>\n'

preview_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aviation Weather Forecasting — Module 1 Preview</title>
<style>
/* ── Design tokens ── */
:root {{
  --bg:#fff; --surface:#f6f5f0; --border:#e2dfd6; --text:#1a1917;
  --muted:#6b6a65; --accent:#185fa5; --accent-light:#e6f1fb;
  --note-bg:#e1f5ee; --note-border:#0F6E56; --warn-bg:#faeeda;
  --warn-border:#BA7517; --key-bg:#EEEDFE; --key-border:#534AB7;
  --sidebar-w:280px;
}}
@media (prefers-color-scheme:dark) {{ :root {{
  --bg:#1a1917; --surface:#242320; --border:#3a3835; --text:#e8e6df;
  --muted:#9a9890; --accent-light:#042c53; --note-bg:#04342c;
  --warn-bg:#412402; --key-bg:#26215c;
}} }}

*, *::before, *::after {{ box-sizing:border-box; }}
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  background:var(--bg); color:var(--text); line-height:1.75; font-size:16px; }}

/* ── Top Bar ── */
.topbar {{
  background:var(--accent); color:#fff; padding:0.6rem 1.5rem;
  display:flex; align-items:center; gap:1rem; position:sticky; top:0; z-index:100;
  box-shadow:0 2px 8px rgba(0,0,0,0.15);
}}
.topbar-logo {{ font-weight:700; font-size:1.1rem; letter-spacing:-0.02em; }}
.topbar-course {{ font-size:0.85rem; opacity:0.85; }}
.topbar-badge {{
  margin-left:auto; background:rgba(255,255,255,0.18); border-radius:4px;
  padding:0.2rem 0.6rem; font-size:0.75rem; font-weight:600;
}}

/* ── Layout ── */
.layout {{ display:flex; min-height:calc(100vh - 44px); }}

/* ── Sidebar ── */
.sidebar {{
  width:var(--sidebar-w); min-width:var(--sidebar-w);
  background:var(--surface); border-right:1px solid var(--border);
  padding:1.25rem 0; overflow-y:auto; position:sticky; top:44px;
  height:calc(100vh - 44px);
}}
.sidebar h3 {{
  font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em;
  color:var(--muted); padding:0 1.25rem; margin:1.2rem 0 0.5rem;
}}
.sidebar h3:first-child {{ margin-top:0; }}
.nav-item {{
  display:flex; align-items:center; gap:0.6rem;
  padding:0.5rem 1.25rem; cursor:pointer; font-size:0.88rem;
  border-left:3px solid transparent; transition:all 0.15s;
}}
.nav-item:hover {{ background:var(--border); }}
.nav-item.active {{ border-left-color:var(--accent); background:var(--accent-light); font-weight:600; }}
.nav-item .icon {{ width:20px; text-align:center; flex-shrink:0; }}
.nav-item.disabled {{ opacity:0.45; cursor:not-allowed; }}
.nav-item.disabled:hover {{ background:transparent; }}

.nav-divider {{ height:1px; background:var(--border); margin:0.75rem 1.25rem; }}

.future-badge {{
  display:inline-block; background:var(--warn-bg); border:1px solid var(--warn-border);
  color:var(--text); font-size:0.65rem; font-weight:600; padding:0.1rem 0.4rem;
  border-radius:3px; margin-left:auto; text-transform:uppercase;
}}

/* ── Content ── */
.content {{ flex:1; max-width:900px; margin:0 auto; padding:2rem 2.5rem; }}

/* ── Lesson page styles (inherited from lesson CSS) ── */
h1 {{ font-size:1.8rem; font-weight:600; }}
h2 {{ font-size:1.25rem; font-weight:600; margin-top:2.5rem;
  padding-bottom:0.4rem; border-bottom:1.5px solid var(--border); }}
h3 {{ font-size:1.05rem; font-weight:600; margin-top:1.75rem; }}
p {{ margin:0.7rem 0; max-width:72ch; }}
figure {{ margin:2rem 0; }}
figcaption {{ font-size:0.85rem; color:var(--muted); margin-top:0.6rem;
  font-style:italic; text-align:center; }}
svg {{ max-width:100%; height:auto; display:block; margin:0 auto; }}
table {{ border-collapse:collapse; width:100%; margin:1.5rem 0; font-size:0.9rem; }}
th {{ background:var(--accent); color:#fff; padding:0.55rem 0.9rem; text-align:left; }}
td {{ padding:0.5rem 0.9rem; border-bottom:1px solid var(--border); }}
tr:nth-child(even) td {{ background:var(--surface); }}
img {{ max-width:100%; height:auto; }}
.callout {{ border-radius:8px; padding:1rem 1.25rem; margin:1.5rem 0; }}
.callout-note    {{ background:var(--note-bg);  border-left:4px solid var(--note-border); }}
.callout-warning {{ background:var(--warn-bg);  border-left:4px solid var(--warn-border); }}
.callout-key     {{ background:var(--key-bg);   border-left:4px solid var(--key-border); }}
.objectives {{ background:var(--surface); border-radius:8px; padding:1.25rem 1.5rem; margin:1.5rem 0; }}
.lesson-summary {{ background:var(--accent-light); border-radius:8px;
  padding:1.25rem 1.5rem; margin:2.5rem 0 1rem; }}

/* ── Quiz styles ── */
.quiz-header {{ margin-bottom:1.5rem; }}
.quiz-question {{
  background:var(--surface); border-radius:8px; padding:1.25rem 1.5rem;
  margin:1.25rem 0; border:1px solid var(--border);
}}
.quiz-question h4 {{ margin:0 0 0.75rem; font-size:0.95rem; color:var(--muted); }}
.quiz-question .q-text {{ margin-bottom:1rem; }}
.quiz-option {{
  display:flex; align-items:flex-start; gap:0.5rem; padding:0.5rem 0.75rem;
  margin:0.3rem 0; border-radius:6px; cursor:pointer; border:1.5px solid transparent;
  transition:all 0.15s;
}}
.quiz-option:hover {{ background:var(--accent-light); }}
.quiz-option input {{ margin-top:0.35rem; }}
.quiz-option.correct {{ border-color:var(--note-border); background:var(--note-bg); }}
.quiz-option.incorrect {{ border-color:#c0392b; background:#fdecea; }}
.quiz-feedback {{
  display:none; margin-top:0.75rem; padding:0.75rem 1rem;
  border-radius:6px; font-size:0.9rem; background:var(--key-bg);
  border-left:3px solid var(--key-border);
}}
.quiz-feedback.visible {{ display:block; }}
.quiz-actions {{ margin-top:1.5rem; text-align:center; }}
.btn {{
  display:inline-block; padding:0.6rem 1.5rem; border:none; border-radius:6px;
  font-size:0.9rem; font-weight:600; cursor:pointer; transition:all 0.15s;
}}
.btn-primary {{ background:var(--accent); color:#fff; }}
.btn-primary:hover {{ filter:brightness(1.15); }}
.quiz-score {{
  display:none; text-align:center; padding:2rem; background:var(--surface);
  border-radius:8px; margin-top:1.5rem;
}}
.quiz-score.visible {{ display:block; }}
.quiz-score .score-num {{ font-size:2.5rem; font-weight:700; color:var(--accent); }}

/* ── Overview (landing) ── */
.overview-hero {{
  background:linear-gradient(135deg, var(--accent) 0%, #1a3a6b 100%);
  color:#fff; padding:2.5rem; border-radius:12px; margin-bottom:2rem;
}}
.overview-hero h1 {{ color:#fff; margin:0 0 0.5rem; }}
.overview-hero p {{ color:rgba(255,255,255,0.85); max-width:60ch; }}
.overview-grid {{
  display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin:1.5rem 0;
}}
.overview-card {{
  background:var(--surface); border:1px solid var(--border); border-radius:8px;
  padding:1.25rem; cursor:pointer; transition:all 0.15s;
}}
.overview-card:hover {{ border-color:var(--accent); transform:translateY(-2px);
  box-shadow:0 4px 12px rgba(0,0,0,0.08); }}
.overview-card h3 {{ margin:0 0 0.3rem; font-size:1rem; }}
.overview-card .duration {{ font-size:0.8rem; color:var(--muted); }}

/* ── Responsive ── */
@media (max-width:900px) {{
  .sidebar {{ display:none; }}
  .overview-grid {{ grid-template-columns:1fr; }}
}}
</style>
</head>
<body>

<!-- Top Bar -->
<div class="topbar">
  <span class="topbar-logo">☁️ IMS Learning</span>
  <span class="topbar-course">Aviation Weather Forecasting Certification</span>
  <span class="topbar-badge">PREVIEW</span>
</div>

<div class="layout">

<!-- Sidebar -->
<nav class="sidebar">
  <h3>Module 1</h3>
  <div class="nav-item active" onclick="showPage('overview')" id="nav-overview">
    <span class="icon">📋</span> Module Overview
  </div>

  <div class="nav-divider"></div>
  <h3>Lessons</h3>
  <div class="nav-item" onclick="showPage('lesson-1')" id="nav-lesson-1">
    <span class="icon">📄</span> 1. Regulatory Frameworks
  </div>
  <div class="nav-item" onclick="showPage('quiz-1')" id="nav-quiz-1">
    <span class="icon">✏️</span> Quiz: Lesson 1
  </div>
  <div class="nav-item" onclick="showPage('lesson-2')" id="nav-lesson-2">
    <span class="icon">📄</span> 2. Route Planning & Fuel
  </div>
  <div class="nav-item" onclick="showPage('quiz-2')" id="nav-quiz-2">
    <span class="icon">✏️</span> Quiz: Lesson 2
  </div>
  <div class="nav-item" onclick="showPage('lesson-3')" id="nav-lesson-3">
    <span class="icon">📄</span> 3. Airspace Structure
  </div>
  <div class="nav-item" onclick="showPage('quiz-3')" id="nav-quiz-3">
    <span class="icon">✏️</span> Quiz: Lesson 3
  </div>
  <div class="nav-item" onclick="showPage('lesson-4')" id="nav-lesson-4">
    <span class="icon">📄</span> 4. Altimetry
  </div>
  <div class="nav-item" onclick="showPage('quiz-4')" id="nav-quiz-4">
    <span class="icon">✏️</span> Quiz: Lesson 4
  </div>

  <div class="nav-divider"></div>
  <h3>Coming Soon</h3>
  <div class="nav-item disabled">
    <span class="icon">🔒</span> Module 2: In-flight Hazards <span class="future-badge">Soon</span>
  </div>
  <div class="nav-item disabled">
    <span class="icon">🔒</span> Module 3: Terminal Visibility <span class="future-badge">Soon</span>
  </div>
  <div class="nav-item disabled">
    <span class="icon">🔒</span> Module 4: Products & Warnings <span class="future-badge">Soon</span>
  </div>
</nav>

<!-- Main Content -->
<main class="content">

  <!-- Overview Page -->
  <div class="lesson-page" id="overview" style="display:block;">
    <div class="overview-hero">
      <h1>Module 1: Aviation Weather Fundamentals & Regulations</h1>
      <p>Welcome to the first module of the Aviation Weather Forecasting Certification course. This self-paced module covers international regulatory frameworks, route planning, airspace structures, and altimetry principles.</p>
      <p style="margin-top:1rem; font-size:0.85rem; opacity:0.7;">Estimated total time: ~100 minutes &nbsp;|&nbsp; 4 Lessons &nbsp;|&nbsp; 16 Quiz Questions &nbsp;|&nbsp; Pass mark: 75%</p>
    </div>

    <h2>Curriculum</h2>
    <div class="overview-grid">
      <div class="overview-card" onclick="showPage('lesson-1')">
        <h3>📄 Lesson 1: International Regulatory Frameworks</h3>
        <p style="font-size:0.88rem; margin:0.3rem 0;">WMO & ICAO roles, Annex 3 compliance, Standards and Recommended Practices.</p>
        <span class="duration">⏱ 25 min &nbsp;|&nbsp; 5 quiz questions</span>
      </div>
      <div class="overview-card" onclick="showPage('lesson-2')">
        <h3>📄 Lesson 2: Route Planning & Fuel Management</h3>
        <p style="font-size:0.88rem; margin:0.3rem 0;">Headwinds/tailwinds, temperature effects on performance, fuel contingency.</p>
        <span class="duration">⏱ 30 min &nbsp;|&nbsp; 4 quiz questions</span>
      </div>
      <div class="overview-card" onclick="showPage('lesson-3')">
        <h3>📄 Lesson 3: Airspace Structure & Classification</h3>
        <p style="font-size:0.88rem; margin:0.3rem 0;">FIRs, airspace classes A-G, VFR/IFR minimums, special use airspace.</p>
        <span class="duration">⏱ 20 min &nbsp;|&nbsp; 4 quiz questions</span>
      </div>
      <div class="overview-card" onclick="showPage('lesson-4')">
        <h3>📄 Lesson 4: Principles of Aviation Altimetry</h3>
        <p style="font-size:0.88rem; margin:0.3rem 0;">QNH, QFE, QNE, transition altitudes/levels, cold weather errors.</p>
        <span class="duration">⏱ 25 min &nbsp;|&nbsp; 3 quiz questions</span>
      </div>
    </div>

    <h2>Module Competencies</h2>
    <div class="callout callout-key">
      <p style="margin:0;">Upon completion you will be certified to:</p>
      <ul style="margin:0.5rem 0 0;">
        <li>Navigate and apply WMO/ICAO regulatory frameworks governing aeronautical meteorology.</li>
        <li>Integrate meteorological factors into fuel consumption and route optimization.</li>
        <li>Assess airspace classifications and route structures to support aviation planning.</li>
        <li>Calculate and apply correct altimetry settings for safe flight operations.</li>
      </ul>
    </div>

    <h2 style="margin-top:2.5rem;">Course Roadmap</h2>
    <table>
      <thead><tr><th>Module</th><th>Topics</th><th>Status</th></tr></thead>
      <tbody>
        <tr><td><strong>Module 1: Fundamentals & Regulations</strong></td><td>WMO/ICAO, Routes & Fuel, Airspace, Altimetry</td><td style="color:var(--note-border); font-weight:600;">✅ Available</td></tr>
        <tr><td>Module 2: In-flight Aviation Hazards</td><td>Turbulence, Icing, CB Clouds, Wind Shear, Volcanic Ash</td><td style="color:var(--warn-border);">🚧 Under Construction</td></tr>
        <tr><td>Module 3: Terminal Area Hazards & Visibility</td><td>Fog, Haze, Cloud Base & Top Forecasting</td><td style="color:var(--warn-border);">🚧 Under Construction</td></tr>
        <tr><td>Module 4: Forecast Products & Warnings</td><td>Area & Aerodrome Warnings, TAF Writing, Tropical Storms, WAFC Maps</td><td style="color:var(--warn-border);">🚧 Under Construction</td></tr>
      </tbody>
    </table>
  </div>

  <!-- Lesson Pages -->
  {lesson_sections}

  <!-- Quiz Pages -->
  {quiz_containers}

</main>
</div>

<script>
// Quiz data
const quizData = {quiz_json};

// Navigation
function showPage(pageId) {{
  document.querySelectorAll('.lesson-page').forEach(el => el.style.display = 'none');
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

  const page = document.getElementById(pageId);
  if (page) {{
    page.style.display = 'block';
    window.scrollTo(0, 0);
  }}

  const navEl = document.getElementById('nav-' + pageId);
  if (navEl) navEl.classList.add('active');

  // If it's a quiz page, render quiz
  if (pageId.startsWith('quiz-')) {{
    const lessonNum = pageId.split('-')[1];
    renderQuiz(lessonNum);
  }}
}}

function renderQuiz(lessonNum) {{
  const lessonKeys = Object.keys(quizData);
  const key = lessonKeys[lessonNum - 1];
  const questions = quizData[key];
  if (!questions) return;

  const container = document.getElementById('quiz-' + lessonNum);
  if (container.dataset.rendered) return;
  container.dataset.rendered = 'true';

  let html = '<div class="quiz-header"><h1>Quiz: Lesson ' + lessonNum + '</h1>';
  html += '<p style="color:var(--muted);">Answer all questions, then click "Check Answers" to see your score and rationale.</p></div>';

  questions.forEach((q, i) => {{
    html += '<div class="quiz-question" id="qq-' + lessonNum + '-' + i + '">';
    html += '<h4>' + q.name + '</h4>';
    html += '<div class="q-text">' + q.question + '</div>';
    q.answers.forEach((a, j) => {{
      const optId = 'opt-' + lessonNum + '-' + i + '-' + j;
      html += '<label class="quiz-option" id="lbl-' + optId + '">';
      html += '<input type="radio" name="q' + lessonNum + '_' + i + '" value="' + j + '" data-correct="' + a.correct + '">';
      html += '<span>' + a.text + '</span>';
      html += '</label>';
    }});
    html += '<div class="quiz-feedback" id="fb-' + lessonNum + '-' + i + '">' + q.feedback + '</div>';
    html += '</div>';
  }});

  html += '<div class="quiz-actions"><button class="btn btn-primary" onclick="checkQuiz(' + lessonNum + ')">Check Answers</button></div>';
  html += '<div class="quiz-score" id="score-' + lessonNum + '"><div class="score-num"></div><div class="score-text"></div></div>';

  container.innerHTML = html;
}}

function checkQuiz(lessonNum) {{
  const lessonKeys = Object.keys(quizData);
  const key = lessonKeys[lessonNum - 1];
  const questions = quizData[key];
  let correct = 0;

  questions.forEach((q, i) => {{
    const radios = document.querySelectorAll('input[name="q' + lessonNum + '_' + i + '"]');
    let answered = false;
    radios.forEach((r, j) => {{
      const label = document.getElementById('lbl-opt-' + lessonNum + '-' + i + '-' + j);
      if (r.checked) {{
        answered = true;
        if (r.dataset.correct === 'true') {{
          correct++;
          if (label) label.classList.add('correct');
        }} else {{
          if (label) label.classList.add('incorrect');
        }}
      }}
      if (r.dataset.correct === 'true' && label) {{
        label.classList.add('correct');
      }}
      r.disabled = true;
    }});
    const fb = document.getElementById('fb-' + lessonNum + '-' + i);
    if (fb) fb.classList.add('visible');
  }});

  const scoreEl = document.getElementById('score-' + lessonNum);
  const pct = Math.round((correct / questions.length) * 100);
  scoreEl.querySelector('.score-num').textContent = correct + ' / ' + questions.length + ' (' + pct + '%)';
  scoreEl.querySelector('.score-text').textContent = pct >= 75 ? '✅ Passed!' : '❌ Below 75% threshold. Review the lessons and try again.';
  scoreEl.classList.add('visible');
}}
</script>

</body>
</html>'''

with open(OUTPUT / "course_preview.html", "w", encoding="utf-8") as f:
    f.write(preview_html)

print("Preview generated at:", OUTPUT / "course_preview.html")
