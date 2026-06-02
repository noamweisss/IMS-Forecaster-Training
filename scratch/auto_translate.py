import os
import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
import xml.etree.ElementTree as ET
import time

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("deep_translator not installed.")
    exit(1)

translator = GoogleTranslator(source='en', target='iw')

def is_translatable(text):
    text = text.strip()
    if not text:
        return False
    # skip if just numbers/symbols
    if all(not c.isalpha() for c in text):
        return False
    return True

def do_translate(text):
    if not is_translatable(text):
        return text
    try:
        time.sleep(0.1)
        res = translator.translate(text)
        return res if res else text
    except Exception as e:
        print(f"Error translating '{text[:30]}': {e}")
        return text

def translate_batch(texts):
    if not texts:
        return []
    
    # Split into chunks of max 4000 chars to stay safe with API limits
    chunks = []
    current_chunk = []
    current_len = 0
    for t in texts:
        if current_len + len(t) + 10 > 4000:
            chunks.append(current_chunk)
            current_chunk = [t]
            current_len = len(t)
        else:
            current_chunk.append(t)
            current_len += len(t) + 10
    if current_chunk:
        chunks.append(current_chunk)
        
    translated_texts = []
    for chunk in chunks:
        separator = " ||| "
        combined = separator.join(chunk)
        try:
            time.sleep(0.3)
            translated = translator.translate(combined)
            parts = re.split(r'\s*\|\|\|\s*', translated)
            parts = [p.strip() for p in parts if p.strip()]
            
            if len(parts) != len(chunk):
                print(f"Batch size mismatch ({len(parts)} vs {len(chunk)}). Falling back to individual.")
                # Fallback to individual
                for t in chunk:
                    translated_texts.append(do_translate(t))
            else:
                translated_texts.extend(parts)
        except Exception as e:
            print(f"Batch translation error: {e}. Falling back to individual.")
            for t in chunk:
                translated_texts.append(do_translate(t))
                
    return translated_texts

def is_inside_svg(element):
    p = element.parent
    while p:
        if p.name == 'svg':
            return True
        p = p.parent
    return False

def translate_html_file(in_path, out_path):
    print(f"Translating HTML: {in_path.name}")
    content = in_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(content, 'html.parser')
    
    translatable_nodes = []
    texts_to_translate = []
    
    for element in soup.find_all(string=True):
        if element.parent.name in ['style', 'script', 'svg', 'path', 'g', 'circle', 'rect']:
            continue
        if is_inside_svg(element):
            continue
            
        original_text = str(element)
        stripped = original_text.strip()
        if is_translatable(stripped):
            translatable_nodes.append((element, original_text, stripped))
            texts_to_translate.append(stripped)
            
    print(f"  Found {len(texts_to_translate)} translatable texts.")
    translated_texts = translate_batch(texts_to_translate)
    
    for (element, original_text, stripped), translated in zip(translatable_nodes, translated_texts):
        new_text = original_text.replace(stripped, translated)
        element.replace_with(NavigableString(new_text))
            
    out_path.write_text(str(soup), encoding="utf-8")

def translate_xml_file(in_path, out_path):
    print(f"Translating XML: {in_path.name}")
    try:
        tree = ET.parse(in_path)
        root = tree.getroot()
        
        nodes_to_translate = []
        texts_to_translate = []
        
        for text_node in root.findall(".//text"):
            if text_node.text and is_translatable(text_node.text):
                nodes_to_translate.append(text_node)
                texts_to_translate.append(text_node.text.strip())
                
        print(f"  Found {len(texts_to_translate)} XML texts.")
        translated_texts = translate_batch(texts_to_translate)
        
        for node, translated in zip(nodes_to_translate, translated_texts):
            node.text = translated
                
        tree.write(out_path, encoding="utf-8", xml_declaration=True)
    except Exception as e:
        print(f"Error parsing XML {in_path}: {e}")

def main():
    course_dir = Path("courses/aviation-weather")
    modules = [1, 2, 3, 4]
    
    for m in modules:
        mod_dir = course_dir / f"module-{m}"
        if not mod_dir.is_dir():
            continue
            
        overview_in = mod_dir / "00_module_overview_moodle.html"
        overview_out = mod_dir / "00_module_overview_moodle_he.html"
        if overview_in.is_file():
            translate_html_file(overview_in, overview_out)
            
        lessons_dir = mod_dir / "lessons"
        if lessons_dir.is_dir():
            for html_file in lessons_dir.glob("*_moodle.html"):
                if html_file.name.endswith("_he.html"):
                    continue
                out_name = html_file.name.replace("_moodle.html", "_moodle_he.html")
                translate_html_file(html_file, lessons_dir / out_name)
                
            for xml_file in lessons_dir.glob("*.xml"):
                if xml_file.name.endswith("_he.xml"):
                    continue
                out_name = xml_file.name.replace(".xml", "_he.xml")
                translate_xml_file(xml_file, lessons_dir / out_name)
                
    print("Translation complete.")

if __name__ == "__main__":
    main()
