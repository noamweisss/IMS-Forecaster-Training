# Pipeline Architecture

The IMS Course Factory pipeline converts raw educational materials (PowerPoint, PDF, Word) into Moodle-ready learning modules using a 4-stage process.

## Pipeline Stages

1. **Extraction**
   - Parses raw source files (PPTX, PDF, DOCX).
   - Extracts structural and textual information like titles, bullet points, and speaker notes.
   - Scripts: `pipeline/extract_content.py` and extraction methods in `pipeline/module_pipeline.py`.

2. **Blueprint**
   - Sends the aggregated summaries to the Claude API.
   - Dynamically designs a comprehensive lesson plan (blueprint) for the module, determining the number of lessons, learning objectives, and quiz requirements.

3. **Content Generation**
   - Processes the extracted content according to the blueprint using the Claude API.
   - Generates visually appealing, Moodle-ready HTML lessons and application-level quiz questions.
   - Runs in parallel for all lessons to save time.

4. **Assembly**
   - Packages the generated HTML lessons, Moodle XML quiz files, overview pages, and supporting documentation into an output directory.
   - Outputs clear instructions for importing into Moodle.
