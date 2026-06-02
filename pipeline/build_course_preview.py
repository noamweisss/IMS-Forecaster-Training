#!/usr/bin/env python3
"""
build_course_preview.py — Compile a full course's Moodle fragments, structures,
and quizzes into a single, highly-polished offline-first Single Page App (SPA)
suitable for hosting on Netlify.

Pure standard library Python. Zero third-party dependencies.
This ensures it runs instantly on local machines and Netlify build servers.

Usage:
    python pipeline/build_course_preview.py --course courses/aviation-weather
"""

import argparse
import base64
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Scrapers for extracting styles and clean bodies from generated fragments
_STYLE_RE   = re.compile(r"<style\b[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
_WRAPPER_RE = re.compile(
    r'<div\s+class="ims-lesson"[^>]*>(.*)</div>\s*$',
    re.DOTALL | re.IGNORECASE,
)
_BREADCRUMB_RE = re.compile(
    r'<p\s+class="breadcrumb"[^>]*>.*?</p>',
    re.DOTALL | re.IGNORECASE,
)

def clean_xml_text(text: str | None) -> str:
    """Strip XML CDATA residue and spaces."""
    if not text:
        return ""
    text = re.sub(r'<!\[CDATA\[', '', text)
    text = re.sub(r'\]\]>', '', text)
    return text.strip()

def split_style_and_body(html: str) -> tuple[str, str]:
    """Extract the inner CSS style block and the core clean body from a fragment."""
    style_match = _STYLE_RE.search(html)
    style = style_match.group(1).strip() if style_match else ""
    
    without_style = _STYLE_RE.sub("", html).strip()
    
    # Strip breadcrumb if present
    without_style = _BREADCRUMB_RE.sub("", without_style, count=1).strip()
    
    wrapper_match = _WRAPPER_RE.search(without_style)
    body = wrapper_match.group(1).strip() if wrapper_match else without_style
    return style, body

def parse_quiz_xml(xml_path: Path) -> list[dict]:
    """Parse a Moodle XML quiz file and convert it to a structured list of questions."""
    questions = []
    if not xml_path.is_file():
        return []
    
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for q in root.findall("question"):
            if q.attrib.get("type") != "multichoice":
                continue
            
            name_node = q.find("name/text")
            name = clean_xml_text(name_node.text) if name_node is not None else ""
            
            qtext_node = q.find("questiontext/text")
            qtext = clean_xml_text(qtext_node.text) if qtext_node is not None else ""
            
            feedback_node = q.find("generalfeedback/text")
            feedback = clean_xml_text(feedback_node.text) if feedback_node is not None else ""
            
            answers = []
            for ans in q.findall("answer"):
                fraction = int(ans.attrib.get("fraction", "0"))
                ans_text_node = ans.find("text")
                ans_text = clean_xml_text(ans_text_node.text) if ans_text_node is not None else ""
                
                answers.append({
                    "text": ans_text,
                    "correct": fraction > 0
                })
            
            questions.append({
                "name": name,
                "question": qtext,
                "feedback": feedback,
                "answers": answers
            })
    except Exception as e:
        print(f"      [Warning] Failed to parse quiz {xml_path.name}: {e}", file=sys.stderr)
        
    return questions

def to_base64_str(text: str) -> str:
    """Safely convert a string to base64 for embedding in the JSON."""
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")

def build_preview(course_path: Path, output_path: Path):
    print(f"Building Course Preview for: {course_path.name}")
    
    course_json_file = course_path / "course.json"
    if not course_json_file.is_file():
        print(f"Error: Missing course.json at {course_json_file}", file=sys.stderr)
        sys.exit(1)
        
    course_meta = json.loads(course_json_file.read_text(encoding="utf-8"))
    
    course_data = {
        "course_id": course_meta.get("course_id", course_path.name),
        "title": course_meta.get("title", "Aviation Weather Forecasting Certification"),
        "target_audience": course_meta.get("target_audience", ""),
        "subject_matter_expert": course_meta.get("subject_matter_expert", ""),
        "modules": []
    }
    
    global_styles = []
    quiz_data = {}
    
    for mod in course_meta.get("modules", []):
        mod_folder = mod.get("folder", f"module-{mod['number']}")
        mod_dir = course_path / mod_folder
        
        module_info = {
            "number": mod["number"],
            "title": mod["title"],
            "status": mod.get("status", "Pending generation"),
            "is_available": False,
            "competencies": [],
            "overview_html_b64": "",
            "lessons": []
        }
        
        # Check if the folder is generated
        structure_file = mod_dir / "module_structure.json"
        overview_file = mod_dir / "00_module_overview_moodle.html"
        lessons_dir = mod_dir / "lessons"
        
        if structure_file.is_file() and overview_file.is_file() and lessons_dir.is_dir():
            module_info["is_available"] = True
            
            # Parse structure to load competencies and syllabus info
            try:
                struct_data = json.loads(structure_file.read_text(encoding="utf-8"))
                module_info["competencies"] = struct_data.get("module_competencies", [])
            except Exception as e:
                print(f"      [Warning] Failed to read structure json in {mod_folder}: {e}")
                
            # Process overview
            overview_raw = overview_file.read_text(encoding="utf-8")
            ov_style, ov_body = split_style_and_body(overview_raw)
            if ov_style:
                global_styles.append(ov_style)
            module_info["overview_html_b64"] = to_base64_str(ov_body)
            
            # Find and sort all lesson moodle files
            moodle_files = sorted(lessons_dir.glob("*_moodle.html"))
            for lf in moodle_files:
                # Extract lesson number and slug
                # Expected format: NN_slug_moodle.html
                match = re.match(r"^(\d+)_(.*)_moodle\.html$", lf.name)
                if not match:
                    continue
                
                les_num = int(match.group(1))
                slug = match.group(2)
                
                # Parse lesson fragment
                les_raw = lf.read_text(encoding="utf-8")
                les_style, les_body = split_style_and_body(les_raw)
                if les_style:
                    global_styles.append(les_style)
                
                # Find title from body h1
                h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", les_body, re.DOTALL | re.IGNORECASE)
                les_title = re.sub(r"<[^>]+>", "", h1_match.group(1)).strip() if h1_match else slug.replace("_", " ").title()
                
                lesson_item = {
                    "number": les_num,
                    "title": les_title,
                    "slug": slug,
                    "html_b64": to_base64_str(les_body),
                    "has_quiz": False
                }
                
                # Try to load corresponding quiz XML
                quiz_file_name = lf.name.replace("_moodle.html", "_quiz.xml")
                quiz_path = lessons_dir / quiz_file_name
                if quiz_path.is_file():
                    questions = parse_quiz_xml(quiz_path)
                    if questions:
                        quiz_key = f"quiz-{mod['number']}-{les_num}"
                        quiz_data[quiz_key] = questions
                        lesson_item["has_quiz"] = True
                
                module_info["lessons"].append(lesson_item)
                
        else:
            # Module under construction, parse from structure if it exists, or just use details from course.json
            if structure_file.is_file():
                try:
                    struct_data = json.loads(structure_file.read_text(encoding="utf-8"))
                    module_info["competencies"] = struct_data.get("module_competencies", [])
                    for les in struct_data.get("lessons", []):
                        module_info["lessons"].append({
                            "number": les["lesson_number"],
                            "title": les["title"],
                            "slug": les.get("source_files", [""])[0].replace(".pdf", "").replace(".pptx", "").lower(),
                            "html_b64": "",
                            "has_quiz": False
                        })
                except Exception:
                    pass
            
            # Ensure lessons list has items if we have none, for mapping the syllabus preview
            if not module_info["lessons"]:
                module_info["lessons"] = [
                    {"number": i, "title": f"Syllabus Topic {i}", "slug": "soon", "html_b64": "", "has_quiz": False}
                    for i in range(1, 4)
                ]
        
        # Sort lessons by number
        module_info["lessons"].sort(key=lambda x: x["number"])
        course_data["modules"].append(module_info)
        
    print(f"      Mapped {len(course_data['modules'])} modules.")
    print(f"      Parsed {len(quiz_data)} interactive quizzes.")
    
    # Merge and deduplicate CSS styles
    merged_css = "\n\n".join(global_styles)
    # Deduplicate common moodle tags from scoping
    # Note: we let them co-exist. The browser parses them sequentially, which is fine since all use standard class names.

    # Build index.html
    html_template = get_spa_template(course_data, quiz_data, merged_css)
    
    output_path.mkdir(parents=True, exist_ok=True)
    index_out = output_path / "index.html"
    index_out.write_text(html_template, encoding="utf-8")
    print(f"      [Success] Generated single-file SPA: {index_out.resolve()}")
    
    # Write netlify.toml
    netlify_toml = output_path / "netlify.toml"
    netlify_toml.write_text("[build]\n  publish = \".\"\n", encoding="utf-8")
    print(f"      [Success] Generated netlify config: {netlify_toml.resolve()}")

def get_spa_template(course_data: dict, quiz_data: dict, merged_css: str) -> str:
    course_json_str = json.dumps(course_data, ensure_ascii=False)
    quiz_json_str = json.dumps(quiz_data, ensure_ascii=False)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{course_data['title']} — Course Preview</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700&display=swap" rel="stylesheet">
<style>
/* ── Premium SPA Shell CSS ── */
:root {{
  --shell-bg: #f8fafc;
  --shell-surface: #ffffff;
  --shell-border: #e2e8f0;
  --shell-text: #0f172a;
  --shell-muted: #64748b;
  --shell-accent: #185fa5;
  --shell-accent-hover: #12487e;
  --shell-accent-light: #eff6ff;
  
  --sidebar-bg: #0f172a;
  --sidebar-text: #f8fafc;
  --sidebar-border: #1e293b;
  --sidebar-accent: #38bdf8;
  --sidebar-accent-light: rgba(56, 189, 248, 0.1);
  --sidebar-muted: #94a3b8;
  
  --sidebar-w: 320px;
  --header-h: 56px;
  --transition-speed: 0.2s;
}}

body.dark-mode {{
  --shell-bg: #0b0f19;
  --shell-surface: #111827;
  --shell-border: #1f2937;
  --shell-text: #f1f5f9;
  --shell-muted: #94a3b8;
  --shell-accent: #3b82f6;
  --shell-accent-hover: #60a5fa;
  --shell-accent-light: #1e293b;
}}

*, *::before, *::after {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--shell-bg);
  color: var(--shell-text);
  line-height: 1.7;
  font-size: 16px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  transition: background var(--transition-speed), color var(--transition-speed);
}}

/* ── Top Bar / Header ── */
header.topbar {{
  background: var(--shell-surface);
  border-bottom: 1px solid var(--shell-border);
  height: var(--header-h);
  padding: 0 1.5rem;
  display: flex;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  transition: background var(--transition-speed), border var(--transition-speed);
}}

.menu-btn {{
  display: none;
  background: transparent;
  border: none;
  font-size: 1.5rem;
  color: var(--shell-text);
  cursor: pointer;
  margin-right: 1rem;
}}

.topbar-logo {{
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  font-size: 1.25rem;
  color: var(--shell-accent);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
}}

.topbar-course {{
  margin-left: 1.5rem;
  padding-left: 1.5rem;
  border-left: 1.5px solid var(--shell-border);
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--shell-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}

.topbar-controls {{
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 1rem;
}}

.theme-toggle {{
  background: transparent;
  border: 1px solid var(--shell-border);
  border-radius: 8px;
  width: 36px;
  height: 36px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--shell-text);
  transition: all var(--transition-speed);
}}

.theme-toggle:hover {{
  background: var(--shell-accent-light);
  border-color: var(--shell-accent);
  color: var(--shell-accent);
}}

.preview-badge {{
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff;
  border-radius: 6px;
  padding: 0.25rem 0.6rem;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}}

/* ── App Layout ── */
.layout {{
  display: flex;
  flex: 1;
  min-height: calc(100vh - var(--header-h));
}}

/* ── Sidebar Navigation ── */
nav.sidebar {{
  width: var(--sidebar-w);
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  color: var(--sidebar-text);
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-h));
  position: sticky;
  top: var(--header-h);
  overflow-y: auto;
  z-index: 90;
  transition: transform var(--transition-speed) ease-in-out;
}}

.sidebar-header-item {{
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  color: var(--sidebar-text);
  border-left: 4px solid transparent;
  transition: all var(--transition-speed);
}}

.sidebar-header-item:hover {{
  background: rgba(255,255,255,0.05);
}}

.sidebar-header-item.active {{
  border-left-color: var(--sidebar-accent);
  background: var(--sidebar-accent-light);
  color: var(--sidebar-accent);
}}

.sidebar-divider {{
  height: 1px;
  background: var(--sidebar-border);
  margin: 0.5rem 0;
}}

.module-group {{
  border-bottom: 1px solid var(--sidebar-border);
}}

.module-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--sidebar-muted);
  transition: background var(--transition-speed), color var(--transition-speed);
}}

.module-header:hover {{
  background: rgba(255,255,255,0.03);
  color: var(--sidebar-text);
}}

.module-header .chevron {{
  font-size: 0.75rem;
  transition: transform var(--transition-speed);
}}

.module-group.collapsed .chevron {{
  transform: rotate(-90deg);
}}

.module-items {{
  display: block;
  overflow: hidden;
  max-height: 1000px;
  transition: max-height 0.3s ease-in-out;
}}

.module-group.collapsed .module-items {{
  max-height: 0;
  display: none;
}}

.nav-subitem {{
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.6rem 1.5rem 0.6rem 2.25rem;
  cursor: pointer;
  font-size: 0.88rem;
  color: var(--sidebar-muted);
  border-left: 4px solid transparent;
  transition: all var(--transition-speed);
}}

.nav-subitem:hover {{
  background: rgba(255,255,255,0.03);
  color: var(--sidebar-text);
}}

.nav-subitem.active {{
  border-left-color: var(--sidebar-accent);
  background: var(--sidebar-accent-light);
  color: var(--sidebar-accent);
  font-weight: 600;
}}

.nav-subitem.disabled {{
  opacity: 0.4;
  cursor: not-allowed;
}}

.nav-subitem.disabled:hover {{
  background: transparent;
  color: var(--sidebar-muted);
}}

.nav-subitem .icon {{
  width: 20px;
  text-align: center;
}}

.status-indicator {{
  font-size: 0.65rem;
  font-weight: 600;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  margin-left: auto;
  text-transform: uppercase;
}}

.status-indicator.soon {{
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}}

/* ── Content Viewport ── */
main.viewport {{
  flex: 1;
  padding: 2.5rem 2rem;
  overflow-y: auto;
  display: flex;
  justify-content: center;
  transition: background var(--transition-speed);
}}

.content-container {{
  width: 100%;
  max-width: 900px;
}}

/* Hide all views by default */
.view-panel {{
  display: none;
}}

.view-panel.active {{
  display: block;
  animation: fadeIn 0.3s ease-in-out;
}}

@keyframes fadeIn {{
  from {{ opacity: 0; transform: translateY(8px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

/* ── Course Overview (Landing) ── */
.landing-hero {{
  background: linear-gradient(135deg, #1e40af 0%, #1e1b4b 100%);
  color: #ffffff;
  padding: 3rem;
  border-radius: 16px;
  margin-bottom: 2.5rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}}

.landing-hero h1 {{
  font-family: 'Outfit', sans-serif;
  font-size: 2.25rem;
  margin: 0 0 0.75rem;
  line-height: 1.2;
}}

.landing-hero p {{
  color: rgba(255,255,255,0.85);
  max-width: 72ch;
  margin: 0 0 1.5rem;
  font-size: 1.05rem;
}}

.landing-meta {{
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  font-size: 0.85rem;
  border-top: 1px solid rgba(255,255,255,0.15);
  padding-top: 1.5rem;
  color: rgba(255,255,255,0.7);
}}

.landing-meta strong {{
  color: #fff;
}}

.curriculum-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}}

.curriculum-card {{
  background: var(--shell-surface);
  border: 1px solid var(--shell-border);
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 5px rgba(0,0,0,0.02);
  transition: all var(--transition-speed);
}}

.curriculum-card:hover {{
  border-color: var(--shell-accent);
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}}

.card-header {{
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}}

.card-header h3 {{
  margin: 0;
  font-family: 'Outfit', sans-serif;
  font-size: 1.15rem;
  color: var(--shell-accent);
}}

.card-badge {{
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
}}

.card-badge.available {{
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}}

.card-badge.soon {{
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}}

.curriculum-card p {{
  font-size: 0.9rem;
  color: var(--shell-muted);
  margin: 0 0 1rem;
}}

.card-syllabus-preview {{
  margin-top: auto;
  border-top: 1px dashed var(--shell-border);
  padding-top: 0.75rem;
  font-size: 0.85rem;
}}

.card-syllabus-preview ul {{
  margin: 0.25rem 0 0;
  padding-left: 1.25rem;
  color: var(--shell-muted);
}}

/* ── Interactive Quiz Views ── */
.quiz-header {{
  border-bottom: 2px solid var(--shell-border);
  padding-bottom: 1rem;
  margin-bottom: 2rem;
}}

.quiz-header h1 {{
  font-family: 'Outfit', sans-serif;
  font-size: 1.8rem;
  margin: 0;
}}

.quiz-question {{
  background: var(--shell-surface);
  border: 1px solid var(--shell-border);
  border-radius: 12px;
  padding: 1.5rem 2rem;
  margin: 1.5rem 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
  transition: all var(--transition-speed);
}}

.quiz-question.checked {{
  box-shadow: none;
}}

.quiz-question h4 {{
  margin: 0 0 0.75rem;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--shell-muted);
}}

.quiz-question .q-text {{
  font-size: 1.05rem;
  font-weight: 500;
  margin-bottom: 1.25rem;
}}

.quiz-option {{
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  margin: 0.5rem 0;
  border-radius: 8px;
  cursor: pointer;
  border: 1.5px solid var(--shell-border);
  background: var(--shell-surface);
  transition: all 0.15s;
}}

.quiz-option:hover {{
  background: var(--shell-accent-light);
  border-color: var(--shell-accent);
}}

.quiz-option input {{
  margin-top: 0.35rem;
  cursor: pointer;
}}

.quiz-option.correct {{
  border-color: #10b981 !important;
  background: rgba(16, 185, 129, 0.08) !important;
  color: #065f46;
}}

body.dark-mode .quiz-option.correct {{
  color: #34d399;
}}

.quiz-option.incorrect {{
  border-color: #ef4444 !important;
  background: rgba(239, 68, 68, 0.08) !important;
  color: #991b1b;
}}

body.dark-mode .quiz-option.incorrect {{
  color: #fca5a5;
}}

.quiz-feedback {{
  display: none;
  margin-top: 1rem;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  font-size: 0.95rem;
  background: var(--shell-accent-light);
  border-left: 4px solid var(--shell-accent);
  animation: slideDown 0.25s ease-out;
}}

.quiz-feedback.visible {{
  display: block;
}}

@keyframes slideDown {{
  from {{ opacity: 0; max-height: 0; }}
  to {{ opacity: 1; max-height: 500px; }}
}}

.quiz-actions {{
  margin-top: 2rem;
  text-align: center;
}}

.btn {{
  display: inline-block;
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-speed);
}}

.btn-primary {{
  background: var(--shell-accent);
  color: #fff;
  box-shadow: 0 4px 6px rgba(24, 95, 165, 0.2);
}}

.btn-primary:hover {{
  background: var(--shell-accent-hover);
  transform: translateY(-1px);
}}

.quiz-score {{
  display: none;
  text-align: center;
  padding: 2.5rem;
  background: var(--shell-surface);
  border: 1px solid var(--shell-border);
  border-radius: 12px;
  margin-top: 2rem;
  animation: fadeIn 0.4s ease;
}}

.quiz-score.visible {{
  display: block;
}}

.quiz-score .score-num {{
  font-size: 3rem;
  font-weight: 700;
  color: var(--shell-accent);
  margin-bottom: 0.5rem;
}}

.quiz-score .score-text {{
  font-size: 1.1rem;
  font-weight: 600;
}}

/* ── Responsive Styling ── */
@media (max-width: 992px) {{
  header.topbar {{
    padding: 0 1rem;
  }}
  .menu-btn {{
    display: block;
  }}
  nav.sidebar {{
    position: fixed;
    top: var(--header-h);
    left: 0;
    transform: translateX(-100%);
    box-shadow: 4px 0 15px rgba(0,0,0,0.1);
  }}
  nav.sidebar.mobile-open {{
    transform: translateX(0);
  }}
  main.viewport {{
    padding: 1.5rem 1rem;
  }}
  .curriculum-grid {{
    grid-template-columns: 1fr;
  }}
  .landing-hero {{
    padding: 2rem;
  }}
}}

/* ── Inline Moodle Lesson CSS overrides and scopes ── */
{merged_css}
</style>
</head>
<body>

<!-- Header -->
<header class="topbar">
  <button class="menu-btn" onclick="toggleSidebar()" aria-label="Toggle Navigation">☰</button>
  <a href="#" class="topbar-logo" onclick="showView('course-landing')">☁️ IMS Learning</a>
  <span class="topbar-course">{course_data['title']}</span>
  
  <div class="topbar-controls">
    <button class="theme-toggle" id="lang-toggle-btn" onclick="toggleLanguage()" title="Toggle Hebrew/English">א</button>
    <button class="theme-toggle" onclick="toggleDarkMode()" title="Toggle Dark/Light Mode">🌓</button>
    <span class="preview-badge">PREVIEW</span>
  </div>
</header>

<div class="layout">
  <!-- Sidebar Navigation -->
  <nav class="sidebar" id="sidebar">
    <div class="sidebar-header-item active" id="nav-course-landing" onclick="showView('course-landing')">
      <span class="icon">🏛️</span> Course Overview
    </div>
    
    <div class="sidebar-divider"></div>
    
    <!-- Rendered Modules List -->
    <div id="sidebar-curriculum-container"></div>
  </nav>

  <!-- Main Viewport -->
  <main class="viewport">
    <div class="content-container">
    
      <!-- Course Overview landing page -->
      <div class="view-panel active" id="course-landing">
        <div class="landing-hero">
          <h1>{course_data['title']}</h1>
          <p>{course_data['target_audience']}</p>
          <div class="landing-meta">
            <div>SME: <strong>{course_data['subject_matter_expert']}</strong></div>
            <div>Structure: <strong>{len(course_data['modules'])} Modules</strong></div>
            <div>Platform: <strong>Moodle Certified</strong></div>
          </div>
        </div>
        
        <h2>Course Syllabus</h2>
        <div class="curriculum-grid" id="landing-syllabus-grid"></div>
        
        <h2>Global Competencies</h2>
        <div class="callout callout-key" style="margin-top: 1rem; border-radius: 12px; padding: 1.5rem;">
          <p style="margin:0; font-weight: 600;">Aviation Weather Certification Goals:</p>
          <ul style="margin: 0.5rem 0 0; padding-left: 1.25rem;">
            <li>Standardization according to ICAO Annex 3 and WMO-No. 49 regulations.</li>
            <li>Operational meteorology application for flight risk assessment and route planning.</li>
            <li>Critical evaluation of atmospheric hazards (turbulence, CB convection, icing, visibility).</li>
            <li>Aviation warning message authoring (TAF, SIGMET, AIRMET) inside national forecast centers.</li>
          </ul>
        </div>
      </div>
      
      <!-- Module Overviews, Lessons, and Quizzes Containers will be dynamically generated here -->
      <div id="dynamic-views-container"></div>

    </div>
  </main>
</div>

<script>
// SPA Shell Engine
const courseData = {course_json_str};
const quizData = {quiz_json_str};

// Base64 helper for decoding built-in fragment strings
function decodeHTML(b64Str) {{
  if (!b64Str) return "";
  try {{
    return atob(b64Str);
  }} catch(e) {{
    // Fallback for UTF-8 bounds
    return decodeURIComponent(escape(atob(b64Str)));
  }}
}}

// Initialize theme
if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {{
  document.body.classList.add('dark-mode');
}}

function applyLanguage(lang) {{
  if (typeof courseDataHe === 'undefined' || typeof courseDataEn === 'undefined') {{
    console.warn("Bilingual data not found.");
    return;
  }}
  const html = document.documentElement;
  if (lang === 'he') {{
    html.setAttribute('lang', 'he');
    html.setAttribute('dir', 'rtl');
    courseData = courseDataHe;
    quizData = quizDataHe;
  }} else {{
    html.setAttribute('lang', 'en');
    html.setAttribute('dir', 'ltr');
    courseData = courseDataEn;
    quizData = quizDataEn;
  }}
  const btn = document.getElementById('lang-toggle-btn');
  if (btn) {{ btn.textContent = lang === 'he' ? 'A' : 'א'; }}
  try {{ localStorage.setItem('preview-lang', lang); }} catch (e) {{}}
}}

function toggleLanguage() {{
  const current = document.documentElement.getAttribute('dir') === 'rtl' ? 'he' : 'en';
  const next = current === 'he' ? 'en' : 'he';
  applyLanguage(next);

  // Capture which view is active *before* re-rendering, then restore it.
  const active = document.querySelector('.view-panel.active');
  const activeId = active ? active.id : 'course-landing';

  generateCourseHTML();
  showView(activeId);
}}

function toggleDarkMode() {{
  document.body.classList.toggle('dark-mode');
}}

function toggleSidebar() {{
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('mobile-open');
}}

// Navigation active tabs
function showView(viewId) {{
  // Hide all panels
  document.querySelectorAll('.view-panel').forEach(el => el.classList.remove('active'));
  
  // Show target panel
  const targetPanel = document.getElementById(viewId);
  if (targetPanel) {{
    targetPanel.classList.add('active');
    window.scrollTo(0, 0);
  }}
  
  // Highlight sidebar
  document.querySelectorAll('.sidebar-header-item, .nav-subitem').forEach(el => el.classList.remove('active'));
  
  const navItem = document.getElementById('nav-' + viewId);
  if (navItem) {{
    navItem.classList.add('active');
    
    // Auto-expand module accordion if selected a lesson inside it
    if (viewId.includes('-')) {{
      const parts = viewId.split('-');
      const modNum = parts[1];
      const modGroup = document.getElementById('mod-group-' + modNum);
      if (modGroup) {{
        modGroup.classList.remove('collapsed');
      }}
    }}
  }}
  
  // Close mobile menu
  document.getElementById('sidebar').classList.remove('mobile-open');
}}

function toggleModuleGroup(modNum) {{
  const group = document.getElementById('mod-group-' + modNum);
  if (group) {{
    group.classList.toggle('collapsed');
  }}
}}

// Assemble UI from raw courseData
function generateCourseHTML() {{
  const sidebarContainer = document.getElementById('sidebar-curriculum-container');
  const syllabusGrid = document.getElementById('landing-syllabus-grid');
  const viewsContainer = document.getElementById('dynamic-views-container');
  
  const isRTL = document.documentElement.getAttribute('dir') === 'rtl';
  
  // Dynamic translations of landing pages static texts
  const heroH1 = document.querySelector('.landing-hero h1');
  const heroP = document.querySelector('.landing-hero p');
  const smeLabel = document.querySelector('.landing-meta div:nth-child(1)');
  const structLabel = document.querySelector('.landing-meta div:nth-child(2)');
  const platLabel = document.querySelector('.landing-meta div:nth-child(3)');
  const syllabusTitle = document.querySelector('.view-panel h2:nth-of-type(1)');
  const competenciesTitle = document.querySelector('.view-panel h2:nth-of-type(2)');
  const compGoalHeader = document.querySelector('.callout-key p');
  const compGoals = document.querySelectorAll('.callout-key li');
  const landingNavText = document.getElementById('nav-course-landing');
  
  if (heroH1) {{ heroH1.textContent = courseData.title; }}
  if (heroP) {{ heroP.textContent = courseData.target_audience; }}
  if (smeLabel) {{ smeLabel.innerHTML = isRTL ? `מומחה תוכן: <strong>${{courseData.subject_matter_expert}}</strong>` : `SME: <strong>${{courseData.subject_matter_expert}}</strong>`; }}
  if (structLabel) {{ structLabel.innerHTML = isRTL ? `מבנה: <strong>4 מודולים</strong>` : `Structure: <strong>4 Modules</strong>`; }}
  if (platLabel) {{ platLabel.innerHTML = isRTL ? `פלטפורמה: <strong>מאושר Moodle</strong>` : `Platform: <strong>Moodle Certified</strong>`; }}
  if (syllabusTitle) {{ syllabusTitle.textContent = isRTL ? `סילבוס הקורס` : `Course Syllabus`; }}
  if (competenciesTitle) {{ competenciesTitle.textContent = isRTL ? `כשרויות גלובליות` : `Global Competencies`; }}
  if (compGoalHeader) {{ compGoalHeader.textContent = isRTL ? `יעדי הסמכת מזג אוויר תעופתי:` : `Aviation Weather Certification Goals:`; }}
  if (landingNavText) {{ landingNavText.innerHTML = isRTL ? `<span class="icon">🏛️</span> סקירת קורס` : `<span class="icon">🏛️</span> Course Overview`; }}
  
  const hebrewGoals = [
    "תקינה לפי תקנות ICAO Annex 3 ו-WMO-No. 49.",
    "יישום מטאורולוגיה מבצעית להערכת סיכוני טיסה ותכנון נתיבים.",
    "הערכה קריטית של מפגעי אטמוספירה (מערבולות, התפתחות ענני CB, התקרחות, ראות).",
    "ניסוח הודעות אזהרה תעופתיות (TAF, SIGMET, AIRMET) במרכזי חיזוי לאומיים."
  ];
  const englishGoals = [
    "Standardization according to ICAO Annex 3 and WMO-No. 49 regulations.",
    "Operational meteorology application for flight risk assessment and route planning.",
    "Critical evaluation of atmospheric hazards (turbulence, CB convection, icing, visibility).",
    "Aviation warning message authoring (TAF, SIGMET, AIRMET) inside national forecast centers."
  ];
  
  if (compGoals && compGoals.length === 4) {{
    compGoals.forEach((li, idx) => {{
      li.textContent = isRTL ? hebrewGoals[idx] : englishGoals[idx];
    }});
  }}
  
  let sidebarHTML = "";
  let gridHTML = "";
  let panelsHTML = "";
  
  courseData.modules.forEach(mod => {{
    const statusText = mod.is_available ? (isRTL ? "זמין" : "Available") : (isRTL ? "בקרוב" : "Soon");
    const badgeClass = mod.is_available ? "available" : "soon";
    const statusIcon = mod.is_available ? "✅" : "🚧";
    
    // Sidebar Module Accordion
    sidebarHTML += `
      <div class="module-group collapsed" id="mod-group-${{mod.number}}">
        <div class="sidebar-divider"></div>
        <div class="module-header" onclick="toggleModuleGroup(${{mod.number}})">
          <span>${{isRTL ? 'מ' : 'M'}}${{mod.number}}: ${{mod.title.split(":")[0] || mod.title}}</span>
          <span class="chevron">▼</span>
        </div>
        <div class="module-items">
          <div class="nav-subitem" id="nav-module-overview-${{mod.number}}" onclick="showView('module-overview-${{mod.number}}')">
            <span class="icon">📋</span> ${{isRTL ? 'סקירת מודול' : 'Module Overview'}}
          </div>
    `;
    
    // Landing Syllabus Cards
    gridHTML += `
      <div class="curriculum-card" onclick="${{mod.is_available ? `showView('module-overview-\${{mod.number}}')` : ""}}">
        <div class="card-header">
          <h3>${{isRTL ? 'מודול' : 'Module'}} ${{mod.number}}: ${{mod.title}}</h3>
          <span class="card-badge ${{badgeClass}}">${{statusText}}</span>
        </div>
        <p>${{mod.competencies[0] || (isRTL ? "סילבוס יופק בהמשך." : "Syllabus pending generation.")}}</p>
        <div class="card-syllabus-preview">
          <strong>${{isRTL ? 'שיעורים כלולים:' : 'Lessons included:'}}</strong>
          <ul>
    `;
    
    // Overview Panel
    let overviewBody = "";
    if (mod.is_available) {{
      overviewBody = decodeHTML(mod.overview_html_b64);
    }} else {{
      overviewBody = `
        <div class="landing-hero" style="background: linear-gradient(135deg, #d97706 0%, #78350f 100%);">
          <h1>🚧 ${{isRTL ? 'מודול' : 'Module'}} ${{mod.number}}: ${{isRTL ? 'בבנייה' : 'Under Construction'}}</h1>
          <p>${{isRTL ? 'מודול זה נמצא כעת בשלבי הפקה בצינור התוכן של הקורס.' : 'This module is currently pending generation in the course pipeline.'}}</p>
        </div>
        <h2>${{isRTL ? 'תצוגה מקדימה של תוכנית הלימודים' : 'Curriculum Preview'}}</h2>
        <ul>
          ${{mod.lessons.map(les => `<li><strong>${{isRTL ? 'שיעור' : 'Lesson'}} \${{les.number}}:</strong> \${{les.title}}</li>`).join("")}}
        </ul>
      `;
    }}
    
    panelsHTML += `
      <div class="view-panel view-html ims-lesson" id="module-overview-${{mod.number}}">
        ${{overviewBody}}
      </div>
    `;
    
    // Process Lessons
    mod.lessons.forEach(les => {{
      const lessonId = `lesson-${{mod.number}}-${{les.number}}`;
      const quizId = `quiz-${{mod.number}}-${{les.number}}`;
      
      gridHTML += `<li>${{isRTL ? 'שיעור' : 'Lesson'}} ${{les.number}}: ${{les.title}}</li>`;
      
      if (mod.is_available) {{
        // Sidebar lesson links
        sidebarHTML += `
          <div class="nav-subitem" id="nav-${{lessonId}}" onclick="showView('${{lessonId}}')">
            <span class="icon">📄</span> ${{les.number}}. ${{les.title.split(":")[0] || les.title}}
          </div>
        `;
        
        // Dynamic Lesson Panels
        panelsHTML += `
          <div class="view-panel view-html ims-lesson" id="${{lessonId}}">
            ${{decodeHTML(les.html_b64)}}
          </div>
        `;
        
        if (les.has_quiz) {{
          sidebarHTML += `
            <div class="nav-subitem" id="nav-${{quizId}}" onclick="showView('${{quizId}}')">
              <span class="icon">✏️</span> ${{isRTL ? 'בוחן' : 'Quiz'}}: ${{isRTL ? 'שיעור' : 'Lesson'}} ${{les.number}}
            </div>
          `;
          
          // Dynamic Quiz Panels (containers to be populated by Javascript)
          panelsHTML += `
            <div class="view-panel" id="${{quizId}}">
              <div class="quiz-header">
                <h1>${{isRTL ? 'בוחן אינטראקטיבי: שיעור' : 'Interactive Quiz: Lesson'}} ${{les.number}}</h1>
                <p style="color:var(--shell-muted); margin-top: 0.25rem;">${{isRTL ? 'בחן את הידע שלך בזמן אמת. קבל ציון של 75% ומעלה כדי לעבור.' : 'Test your knowledge in real-time. Score 75% or higher to pass.'}}</p>
              </div>
              <div id="quiz-container-${{mod.number}}-${{les.number}}"></div>
              <div class="quiz-actions">
                <button class="btn btn-primary" onclick="gradeQuiz(${{mod.number}}, ${{les.number}})">${{isRTL ? 'בדוק תשובות' : 'Check Answers'}}</button>
              </div>
              <div class="quiz-score" id="score-box-${{mod.number}}-${{les.number}}">
                <div class="score-num" id="score-num-${{mod.number}}-${{les.number}}">0 / 0</div>
                <div class="score-text" id="score-text-${{mod.number}}-${{les.number}}">Passed!</div>
              </div>
            </div>
          `;
        }}
      }} else {{
        sidebarHTML += `
          <div class="nav-subitem disabled" title="${{isRTL ? 'בבנייה' : 'Under Construction'}}">
            <span class="icon">🔒</span> ${{les.number}}. ${{les.title}} <span class="status-indicator soon">${{isRTL ? 'בקרוב' : 'Soon'}}</span>
          </div>
        `;
      }}
    }});
    
    sidebarHTML += `
        </div>
      </div>
    `;
    gridHTML += `
          </ul>
        </div>
      </div>
    `;
  }});
  
  sidebarContainer.innerHTML = sidebarHTML;
  syllabusGrid.innerHTML = gridHTML;
  viewsContainer.innerHTML = panelsHTML;
  
  // Bootstrap Quiz render
  courseData.modules.forEach(mod => {{
    if (mod.is_available) {{
      mod.lessons.forEach(les => {{
        if (les.has_quiz) {{
          renderQuizQuestions(mod.number, les.number);
        }}
      }});
    }}
  }});
}}

// Quiz rendering engine
function renderQuizQuestions(modNum, lesNum) {{
  const key = `quiz-${{modNum}}-${{lesNum}}`;
  const questions = quizData[key];
  if (!questions) return;
  
  const container = document.getElementById(`quiz-container-${{modNum}}-${{lesNum}}`);
  let html = "";
  
  const isRTL = document.documentElement.getAttribute('dir') === 'rtl';
  
  questions.forEach((q, qIdx) => {{
    html += `
      <div class="quiz-question" id="q-card-${{modNum}}-${{lesNum}}-${{qIdx}}">
        <h4>${{q.name}}</h4>
        <div class="q-text">${{q.question}}</div>
        <div class="q-options-container">
    `;
    
    q.answers.forEach((ans, ansIdx) => {{
      const optId = `opt-${{modNum}}-${{lesNum}}-${{qIdx}}-${{ansIdx}}`;
      html += `
        <label class="quiz-option" id="label-${{optId}}">
          <input type="radio" name="q-${{modNum}}-${{lesNum}}-${{qIdx}}" id="${{optId}}" value="${{ansIdx}}" data-correct="${{ans.correct}}">
          <span>${{ans.text}}</span>
        </label>
      `;
    }});
    
    html += `
        </div>
        <div class="quiz-feedback" id="feedback-${{modNum}}-${{lesNum}}-${{qIdx}}">
          <strong>${{isRTL ? 'משוב והסבר:' : 'Review & Rationale:'}}</strong>
          <div style="margin-top:0.4rem;">${{q.feedback}}</div>
        </div>
      </div>
    `;
  }});
  
  container.innerHTML = html;
}}

function gradeQuiz(modNum, lesNum) {{
  const key = `quiz-${{modNum}}-${{lesNum}}`;
  const questions = quizData[key];
  let correctCount = 0;
  
  const isRTL = document.documentElement.getAttribute('dir') === 'rtl';
  
  questions.forEach((q, qIdx) => {{
    const radios = document.getElementsByName(`q-${{modNum}}-${{lesNum}}-${{qIdx}}`);
    let answeredIdx = -1;
    
    // Find correct answer index
    let correctIdx = -1;
    q.answers.forEach((ans, idx) => {{
      if (ans.correct) correctIdx = idx;
    }});
    
    for (let r = 0; r < radios.length; r++) {{
      if (radios[r].checked) {{
        answeredIdx = r;
      }}
      radios[r].disabled = true; // lock options
    }}
    
    // Highlight options visually
    q.answers.forEach((ans, ansIdx) => {{
      const label = document.getElementById(`label-opt-${{modNum}}-${{lesNum}}-${{qIdx}}-${{ansIdx}}`);
      if (label) {{
        if (ans.correct) {{
          label.classList.add('correct');
        }} else if (answeredIdx === ansIdx) {{
          label.classList.add('incorrect');
        }}
      }}
    }});
    
    if (answeredIdx === correctIdx) {{
      correctCount++;
    }}
    
    // Reveal feedback
    const fbBox = document.getElementById(`feedback-${{modNum}}-${{lesNum}}-${{qIdx}}`);
    if (fbBox) fbBox.classList.add('visible');
    
    const qCard = document.getElementById(`q-card-${{modNum}}-${{lesNum}}-${{qIdx}}`);
    if (qCard) qCard.classList.add('checked');
  }});
  
  // Show scoreboard
  const pct = Math.round((correctCount / questions.length) * 100);
  const scoreBox = document.getElementById(`score-box-${{modNum}}-${{lesNum}}`);
  const scoreNum = document.getElementById(`score-num-${{modNum}}-${{lesNum}}`);
  const scoreText = document.getElementById(`score-text-${{modNum}}-${{lesNum}}`);
  
  scoreNum.textContent = `${{correctCount}} / ${{questions.length}} (${{pct}}%)`;
  
  if (pct >= 75) {{
    scoreText.innerHTML = isRTL ? "✅ עברת! עבודה מצוינת בהבנת עקרונות החיזוי המבצעיים." : "✅ Passed! Great job understanding the operational forecasting principles.";
    scoreText.style.color = "#10b981";
  }} else {{
    scoreText.innerHTML = isRTL ? "❌ מתחת לציון עובר של 75%. עיין במשוב ונסה שוב." : "❌ Below 75% passing score. Review the rationale feedback and try again.";
    scoreText.style.color = "#ef4444";
  }}
  
  scoreBox.classList.add('visible');
  
  // Smooth scroll to score
  scoreBox.scrollIntoView({{ behavior: 'smooth' }});
}}

// Bootstrap
document.addEventListener('DOMContentLoaded', () => {{
  let savedLang = 'en';
  try {{ savedLang = localStorage.getItem('preview-lang') || 'en'; }} catch (e) {{}}
  applyLanguage(savedLang);

  generateCourseHTML();

  // Default landing view
  showView('course-landing');
}});
</script>

</body>
</html>
"""

def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--course", required=True,
                   help="Path to the course folder containing course.json.")
    p.add_argument("--output", default="preview_dist",
                   help="Directory where the compiled index.html and netlify.toml should be written.")
    args = p.parse_args()
    
    course_path = Path(args.course)
    output_path = Path(args.output)
    
    build_preview(course_path, output_path)

if __name__ == "__main__":
    main()
