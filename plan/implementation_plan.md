# DOCX Form Filling Agent Implementation Plan

The goal is to build a Python application that uses Gemini to extract structured data from diverse source documents and fill DOCX form templates (Hungarian Power of Attorney and Family Tax Benefit Forms).

## Proposed Changes

### Core Engine and Loading
- `app/core/loader.py`: Generic document loading for .txt, .md, .json, .docx, .pdf, and images. Fallback to local OCR if needed.
- `app/core/engine.py`: Gemini integration with retry logic and fallback to basic rule-based extraction. Ensures structured JSON output.
- `app/core/processor.py`: Orchestrates the loading, extraction, normalization, and merge steps.

### Form Handling
- `app/form_utils/detector.py`: Detects form family using keyword spotting (Power-of-attorney vs Family-tax-benefit).
- `app/form_utils/filler.py`: Uses `python-docx` to find and replace placeholders/empty fields inparagraphs and tables. Handles checkboxes.
- `app/adapters/base_adapter.py`: Interface for form-specific field mapping.
- `app/adapters/poa_adapter.py`: Support for `meghatalmazas.docx`.
- `app/adapters/family_tax_adapter.py`: Support for `csaladi_kedvezmeny.docx`.

### CLI and Logging
- `main.py`: CLI using argparse. Handles logging and report generation.

### Demo Data
- `input_data/demo_case/`: Create various fictional documents (text, image, json) to demonstrate system capabilities.

## Verification Plan

### Automated Tests
- `tests/test_detection.py`: Verify form family identification.
- `tests/test_normalization.py`: Verify data merging and normalization schema.
- `tests/test_cli.py`: Smoke test running the full pipeline on both forms.

### Manual Verification
- Visual inspection of `output/filled_*.docx` to ensure formatting is preserved and fields are placed correctly.
- Review `fill_report.json` and `run.log` for correct execution tracking.
