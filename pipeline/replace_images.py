import os
import glob

lessons_dir = 'module_output/lessons'
html_files = glob.glob(os.path.join(lessons_dir, '*.html'))

replacements = [
    ('<img src="images/wmo_icao_assembly.webp" alt="WMO and ICAO assembly" style="width:100%; border-radius:8px;">',
     '<img src="images/wmo_icao_assembly.png" alt="WMO and ICAO assembly" style="width:100%; border-radius:8px;">'),
    ('<div class="image-needed">📷 Needed: Photograph of the UN headquarters or a joint WMO/ICAO assembly to establish the international context.</div>',
     '<figure>\n    <img src="images/wmo_icao_assembly.png" alt="WMO and ICAO assembly" style="width:100%; border-radius:8px;">\n  </figure>'),
    ('<div class="image-needed">📷 Needed: Photograph of a modern airline dispatcher console showing flight tracks overlaid on weather data.</div>',
     '<figure>\n    <img src="images/dispatcher_console.png" alt="Airline dispatcher console with weather data" style="width:100%; border-radius:8px;">\n  </figure>'),
    ('<div class="image-needed">📷 Needed: A 3D graphic showing the "inverted wedding cake" structure of airspace around a major international airport.</div>',
     '<figure>\n    <img src="images/airspace_wedding_cake.png" alt="3D inverted wedding cake airspace structure" style="width:100%; border-radius:8px;">\n  </figure>'),
    ('<div class="image-needed">📷 Needed: Close-up photograph of an aircraft altimeter showing the Kollsman window and pressure setting dial.</div>',
     '<figure>\n    <img src="images/kollsman_window_altimeter.png" alt="Aircraft altimeter with Kollsman window" style="width:100%; border-radius:8px;">\n  </figure>')
]

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    for old_str, new_str in replacements:
        if old_str in content:
            content = content.replace(old_str, new_str)
            modified = True
            
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {os.path.basename(filepath)}')
