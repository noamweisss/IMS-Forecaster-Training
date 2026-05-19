# Skill: Generate a New Module

To generate a new module using the pipeline, follow these steps:

1. **Prepare Source Files**: Place the raw source files (PPTX, PDF, DOCX) in the appropriate `source_files` directory for the course.
2. **Environment**: Ensure you have installed the requirements (`pip install -r requirements.txt`) and set `ANTHROPIC_API_KEY` in your `.env` file.
3. **Execute Pipeline**: Run `pipeline/module_pipeline.py` with the appropriate arguments. Example:
   ```bash
   python pipeline/module_pipeline.py \
       --input courses/aviation-weather/source_files \
       --name "Module Title" \
       --number 2 \
       --course "Aviation Weather Forecasting Certification" \
       --audience "Professional meteorologists seeking Aviation Forecaster certification (IMS)" \
       --output courses/aviation-weather/module-2
   ```
4. **Review Output**: Review the generated `module_structure.json` to ensure the structure is sound.
5. **Human Action**: Provide the user with the generated `README.md` for import instructions and `IMAGES_TO_SOURCE.md` for any required photographs that need manual sourcing.
