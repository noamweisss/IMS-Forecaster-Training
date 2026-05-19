import os
import glob
import xml.etree.ElementTree as ET

lessons_dir = 'module_output/lessons'
xml_files = glob.glob(os.path.join(lessons_dir, '*_quiz.xml'))

root = ET.Element('quiz')

for f in sorted(xml_files):
    tree = ET.parse(f)
    for q in tree.getroot().findall('question'):
        root.append(q)

tree = ET.ElementTree(root)
with open('module_output/module_quiz_all_questions.xml', 'wb') as out:
    out.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
    tree.write(out, encoding='utf-8', xml_declaration=False)
