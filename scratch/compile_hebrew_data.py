import json
import base64
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Scrapers
_STYLE_RE   = re.compile(r"<style\b[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
_WRAPPER_RE = re.compile(
    r'<div\s+class="ims-lesson"[^>]*>(.*)</div>\s*$',
    re.DOTALL | re.IGNORECASE,
)
_BREADCRUMB_RE = re.compile(
    r'<p\s+class="breadcrumb"[^>]*>.*?</p>',
    re.DOTALL | re.IGNORECASE,
)

def clean_xml_text(text):
    if not text: return ""
    text = re.sub(r'<!\[CDATA\[', '', text)
    text = re.sub(r'\]\]>', '', text)
    return text.strip()

def split_style_and_body(html):
    style_match = _STYLE_RE.search(html)
    style = style_match.group(1).strip() if style_match else ""
    without_style = _STYLE_RE.sub("", html).strip()
    without_style = _BREADCRUMB_RE.sub("", without_style, count=1).strip()
    wrapper_match = _WRAPPER_RE.search(without_style)
    body = wrapper_match.group(1).strip() if wrapper_match else without_style
    return style, body

def parse_quiz_xml(xml_path):
    questions = []
    if not xml_path.is_file(): return []
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for q in root.findall("question"):
            if q.attrib.get("type") != "multichoice": continue
            name = clean_xml_text(q.find("name/text").text) if q.find("name/text") is not None else ""
            qtext = clean_xml_text(q.find("questiontext/text").text) if q.find("questiontext/text") is not None else ""
            feedback = clean_xml_text(q.find("generalfeedback/text").text) if q.find("generalfeedback/text") is not None else ""
            answers = []
            for ans in q.findall("answer"):
                fraction = int(ans.attrib.get("fraction", "0"))
                ans_text = clean_xml_text(ans.find("text").text) if ans.find("text") is not None else ""
                answers.append({"text": ans_text, "correct": fraction > 0})
            questions.append({"name": name, "question": qtext, "feedback": feedback, "answers": answers})
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
    return questions

def to_base64_str(text):
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")

def main():
    course_path = Path("courses/aviation-weather")
    he_json_path = course_path / "course_he.json"
    
    if not he_json_path.is_file():
        print("course_he.json not found")
        sys.exit(1)
        
    course_meta = json.loads(he_json_path.read_text(encoding="utf-8"))
    
    course_data = {
        "course_id": course_meta.get("course_id", "aviation-weather"),
        "title": course_meta.get("title", ""),
        "target_audience": course_meta.get("target_audience", ""),
        "subject_matter_expert": course_meta.get("subject_matter_expert", ""),
        "certification_goals": course_meta.get("certification_goals", []),
        "modules": []
    }
    
    quiz_data = {}
    
    for mod in course_meta.get("modules", []):
        mod_dir = course_path / mod.get("folder", f"module-{mod['number']}")
        
        module_info = {
            "number": mod["number"],
            "title": mod["title"],
            "status": mod.get("status", ""),
            "is_available": False,
            "competencies": mod.get("module_competencies", []),
            "overview_html_b64": "",
            "lessons": []
        }

        overview_file = mod_dir / "00_module_overview_moodle_he.html"
        lessons_dir = mod_dir / "lessons"

        if overview_file.is_file() and lessons_dir.is_dir():
            module_info["is_available"] = True
                
            ov_raw = overview_file.read_text(encoding="utf-8")
            _, ov_body = split_style_and_body(ov_raw)
            module_info["overview_html_b64"] = to_base64_str(ov_body)
            
            moodle_files = sorted(lessons_dir.glob("*_moodle_he.html"))
            for lf in moodle_files:
                match = re.match(r"^(\d+)_(.*)_moodle_he\.html$", lf.name)
                if not match: continue
                les_num = int(match.group(1))
                slug = match.group(2)
                
                les_raw = lf.read_text(encoding="utf-8")
                _, les_body = split_style_and_body(les_raw)
                
                h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", les_body, re.DOTALL | re.IGNORECASE)
                les_title = re.sub(r"<[^>]+>", "", h1_match.group(1)).strip() if h1_match else slug.replace("_", " ").title()
                
                lesson_item = {
                    "number": les_num,
                    "title": les_title,
                    "slug": slug,
                    "html_b64": to_base64_str(les_body),
                    "has_quiz": False
                }
                
                quiz_file_name = lf.name.replace("_moodle_he.html", "_quiz_he.xml")
                quiz_path = lessons_dir / quiz_file_name
                if quiz_path.is_file():
                    questions = parse_quiz_xml(quiz_path)
                    if questions:
                        quiz_key = f"quiz-{mod['number']}-{les_num}"
                        quiz_data[quiz_key] = questions
                        lesson_item["has_quiz"] = True
                
                module_info["lessons"].append(lesson_item)
                
        module_info["lessons"].sort(key=lambda x: x["number"])
        course_data["modules"].append(module_info)
        
    # Inject into index.html
    index_file = Path("preview_dist/index.html")
    content = index_file.read_text(encoding="utf-8")
    
    course_json_str = json.dumps(course_data, ensure_ascii=False)
    quiz_json_str = json.dumps(quiz_data, ensure_ascii=False)
    
    # Simple replacement to support bilingual
    if "const courseDataEn" not in content:
        content = content.replace("const courseData =", "const courseDataEn =")
        content = content.replace("const quizData =", "const quizDataEn =")
        
        # Insert Hebrew data and update app state variables AFTER the English variables are fully defined
        injection = f"""
const courseDataHe = {course_json_str};
const quizDataHe = {quiz_json_str};

let courseData = courseDataEn;
let quizData = quizDataEn;
"""
        content = content.replace("// Base64 helper for decoding built-in fragment strings", injection + "\n// Base64 helper for decoding built-in fragment strings")
        
    else:
        # Already injected once, update it
        content = re.sub(r"const courseDataHe = \{.*?\};", f"const courseDataHe = {course_json_str};", content)
        content = re.sub(r"const quizDataHe = \{.*?\};", f"const quizDataHe = {quiz_json_str};", content)
        
    index_file.write_text(content, encoding="utf-8")
    print("Injected courseDataHe into index.html")

if __name__ == "__main__":
    main()
