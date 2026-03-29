# DOCX Form Filling Agent

A practical university-project-grade application for agentic DOCX form understanding and form filling.

## Architecture
- **Loader**: Scans `input_data/` for .txt, .md, .docx, .pdf, and image files.
- **Engine**: Uses Gemini (`google-genai`) to extract structured data into a fixed JSON schema.
- **Processor**: Handles deterministic merging, provenance tracking, and explicit **conflict management**.
- **Filler**: Detects form types and fills placeholders in DOCX templates using `python-docx`.

## Supported Form Families
1. **Hungarian Power of Attorney** (`meghatalmazas.docx`)
2. **Hungarian Family Tax Benefit** (`csaladi_kedvezmeny.docx`)

## How to Run
1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/python3
   pip install -r requirements.txt
   ```
2. Set your `GEMINI_API_KEY` in a `.env` file.
3. Run the CLI:
   ```bash
   # Power of Attorney
   python main.py --form form/meghatalmazas.docx --data input_data/demo_case --output output/poa
   
   # Family Tax Benefit
   python main.py --form form/csaladi_kedvezmeny.docx --data input_data/demo_case --output output/tax
   ```

## Output Artifacts
- `filled_<form_name>.docx`: The filled form.
- `normalized_data.json`: The raw extracted data.
- `fill_report.json`: Execution summary and provenance.
- `output/run.log`: Detailed execution log.

## Extending with New Forms
To add a new form family:
1. Update `app/filler.py`'s `detect_type` method.
2. Add a new mapping in `FormAdapter.get_mapping`.
3. (Optional) Update `app/schema.py` if new data concepts are required.

## Known Limitations
- Placeholder detection is based on token matching and simple heuristics.
- Checkbox marking supports "⎕" replacement.
- Quota limits on the Gemini API may require using lite or preview models.

## Privacy Note
This project is a demonstration. Use fictional/sample data for demos. Recommendation: Use the provided `input_data/demo_case`.
