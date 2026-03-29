Build a complete, runnable Python project directly in the current workspace.

Important:
- Do NOT paste full file contents back into chat unless explicitly asked.
- Create, modify, run, and test files directly in the workspace.
- After implementation, return only:
  1. a short summary of what was built
  2. the final project tree
  3. exact run commands
  4. test results
  5. known limitations

Current workspace structure:
.
├── README.txt
├── form/
│   ├── csaladi_kedvezmeny.docx
│   └── meghatalmazas.docx
├── input_data/
├── output/
└── tananyag/
    └── MIalkfejl_2.pdf

Use this existing structure.
Do not rename these existing directories unless absolutely necessary.
You may create additional source code directories and test directories, but preserve the current top-level folders.

Project context:
README.txt contains the assignment summary.
tananyag/MIalkfejl_2.pdf contains the lecture material.
The two DOCX files in form/ are the two target form families that the system must support as an MVP.

Goal:
Create a practical university-project-grade application for agentic DOCX form understanding and form filling.

Interpretation of the assignment:
This is NOT a fully universal production-grade form filler.
It SHOULD be a generalizable pipeline that:
- accepts a target DOCX form template
- accepts a folder of source documents
- analyzes the form
- finds and interprets likely empty/fillable fields
- extracts relevant information from the source folder
- fills the DOCX while preserving original formatting as much as possible
- works on at least two concrete form families

Required supported form families in MVP:
1. Hungarian power of attorney / authorization form
   - represented by form/meghatalmazas.docx
2. Hungarian family tax benefit declaration form
   - represented by form/csaladi_kedvezmeny.docx

Important design principle:
Use a generic pipeline with:
- generic document loading and extraction
- generic normalized data schema
- generic logging/reporting
- form-family-specific adapters/mappings for the two forms

Do NOT solve this by exact filename matching only.
Do NOT hardcode final filled values.
Do NOT generate a fake demo that bypasses real processing.

Implementation requirements:
- Python 3.10+
- Keep the codebase compact and understandable
- Prefer around 5 to 9 Python files total unless more are clearly justified
- All code, comments, variable names and docstrings must be in English
- Use type hints where helpful
- Use readable, practical design over academic over-engineering

Top-level files/directories that must exist after implementation:
- README.md
- requirements.txt
- main.py
- tests/
- one source package directory (for example app/ or src/)
- keep using the existing form/, input_data/, output/, tananyag/

You may add:
- sample_data/ if useful
- pyproject.toml if useful
- .env.example if useful

Primary AI engine:
Use Gemini API as the primary semantic extraction engine.

Gemini integration rules:
- Read API key from GEMINI_API_KEY environment variable
- If GEMINI_API_KEY is available, Gemini should be the primary engine for:
  - interpreting the form structure and likely field meanings
  - extracting structured data from raw source texts
  - optionally analyzing image files
- If GEMINI_API_KEY is missing or a Gemini call fails, the program must fall back to local heuristics/OCR/rules and still run
- Gemini must return structured data only
- Gemini must NOT directly edit DOCX files

Python must remain responsible for:
- file scanning
- file reading
- OCR invocation
- schema validation
- deterministic merge logic
- DOCX modification
- logging
- report generation

Input and output CLI:
Implement this CLI:

python main.py --form /path/to/form.docx --data /path/to/input_folder --output /path/to/output_folder

Expected output artifacts:
- filled_<original_name>.docx
- normalized_data.json
- fill_report.json
- run.log

Input folder handling requirements:
- Recursively scan the given input folder
- Read and process:
  - .txt
  - .md
  - .json
  - .docx
  - .pdf (best effort text extraction)
  - image files (.png, .jpg, .jpeg) with OCR best effort and/or Gemini multimodal analysis
- If one file is malformed or unreadable, do not crash the whole run
- Log warnings and continue

Because input_data/ is currently empty:
- Create a minimal fictional demo dataset inside input_data/demo_case/
- Use fictional/generated personal data only
- Include multiple files
- Include at least one image input path or sample image file to demonstrate image handling architecture
- The demo should be runnable without real sensitive data

Form analysis requirements:
- Inspect the target DOCX
- Analyze paragraphs and tables
- Detect likely fillable fields/placeholders by content and structure
- Detect the form family by document content, not filename only

Content-based form family detection:
- Power-of-attorney family:
  detect via phrases such as:
  - "MEGHATALMAZÁS"
  - "meghatalmazom"
  - "eljáró hatóság"
  - "ügyben"
- Family-tax-benefit family:
  detect via phrases such as:
  - "Adóelőleg-nyilatkozat"
  - "családi kedvezmény"
  - "adóazonosító"
  - "eltartottak adatai"

Fixed normalized JSON schema:
The normalized JSON schema must be predefined in code and must NOT be invented dynamically at runtime.

Use this exact top-level structure:

{
  "meta": {
    "form_type_detected": "",
    "source_files": [],
    "notes": []
  },
  "people": {
    "principal": {
      "full_name": "",
      "birth_place": "",
      "birth_date": "",
      "mother_name": "",
      "id_number": "",
      "address": "",
      "tax_id": ""
    },
    "agent": {
      "full_name": "",
      "birth_place": "",
      "birth_date": "",
      "mother_name": "",
      "id_number": "",
      "address": "",
      "tax_id": ""
    },
    "taxpayer": {
      "full_name": "",
      "birth_place": "",
      "birth_date": "",
      "mother_name": "",
      "id_number": "",
      "address": "",
      "tax_id": ""
    },
    "partner": {
      "full_name": "",
      "birth_place": "",
      "birth_date": "",
      "mother_name": "",
      "id_number": "",
      "address": "",
      "tax_id": ""
    },
    "witness_1": {
      "full_name": "",
      "address": "",
      "id_number": ""
    },
    "witness_2": {
      "full_name": "",
      "address": "",
      "id_number": ""
    }
  },
  "case": {
    "authority_name": "",
    "case_type": "",
    "city": "",
    "date": ""
  },
  "tax": {
    "submission_year": "",
    "is_modified": false,
    "joint_claim": false,
    "hungary_only_claim": false,
    "disable_contribution_discount": false,
    "discount_amount_huf": "",
    "beneficiary_count": "",
    "employer_name": "",
    "employer_tax_number": "",
    "partner_employer_name": "",
    "partner_employer_tax_number": "",
    "dependents": []
  }
}

Each item in tax.dependents must have this shape:

{
  "tax_id": "",
  "name": "",
  "em_code": "",
  "jj_code": "",
  "change_date": ""
}

Deterministic merge requirements:
- Merge facts from multiple source documents into the fixed schema
- If conflicting values are found for the same field:
  - choose one deterministically
  - record the conflict in logs
  - record a note in normalized_data.json and/or fill_report.json
- Never silently discard conflicts

Extraction requirements:
- Build a generic extraction pipeline
- Collect raw text chunks and metadata about which file they came from
- Prefer one or a few compact Gemini calls instead of many tiny calls
- Validate Gemini JSON output before using it
- If Gemini returns malformed JSON:
  - retry once with a stricter correction prompt
  - if that still fails, fall back to local heuristics

OCR requirements:
- Support OCR best effort for images
- If local OCR is unavailable, do not crash
- If Gemini multimodal is available, it may supplement or replace local OCR for image understanding
- The architecture must visibly support image input even if the demo mostly uses text files

Form adapter requirements:
Create a small adapter system:
- one base adapter abstraction/interface
- one adapter for power-of-attorney forms
- one adapter for family-tax-benefit forms

Generic vs specific balance:
- extraction and normalization must be generic
- mapping from normalized schema to specific DOCX field locations may be form-family-specific
- adding a third form family later should be straightforward

Minimum supported filling for form/meghatalmazas.docx:
- principal full name
- principal birth place
- principal birth date
- principal mother name
- principal id number
- principal address
- agent full name
- agent birth place
- agent birth date
- agent mother name
- agent id number
- agent address
- authority name
- case type
- city
- date
- witness_1 name/address/id
- witness_2 name/address/id

Minimum supported filling for form/csaladi_kedvezmeny.docx:
This can be MVP-level and does NOT need to cover every last detail of the government form.
Support at least:
- taxpayer full name
- taxpayer tax ID
- submission year
- up to 3 dependents
- joint_claim checkbox
- hungary_only_claim checkbox
- disable_contribution_discount checkbox
- discount_amount_huf
- beneficiary_count
- partner full name
- partner tax ID
- employer name
- employer tax number
- partner employer name
- partner employer tax number

If some fields are unsafe or too ambiguous to fill:
- leave them unchanged
- record them in fill_report.json
- do not crash the entire run

Placeholder detection requirements:
Implement practical best-effort DOCX placeholder detection for:
- repeated dots
- underline-like placeholders
- nearby Hungarian field labels
- table cells that appear to contain empty field areas
- checkbox-like characters such as "⎕"

DOCX filling requirements:
- Use python-docx
- Process paragraphs and tables
- Preserve original formatting as much as reasonably possible
- Prefer run-level replacement when possible
- Otherwise do minimal paragraph-level replacement
- Do not rebuild the entire DOCX from scratch unless absolutely necessary

Checkbox handling:
For boolean values in the family tax form:
- implement best-effort checkbox marking, for example replacing "⎕" with "☒" when appropriate
- if exact placement is not reliable, log the limitation instead of failing

Logging and reports:
- Use Python logging
- Write output/run.log
- Save normalized_data.json even if the fill is partial
- Save fill_report.json containing:
  - form type detected
  - fields requested
  - fields filled
  - fields skipped
  - warnings
  - source file used for each filled value if known

Log at least:
- files discovered
- parser used per file
- Gemini usage
- OCR warnings/failures
- form family detection result
- normalized fields found
- fields filled/skipped

Dependencies:
Keep dependencies realistic and minimal.
Use only what is needed, for example:
- python-docx
- pypdf or PyPDF2 or pdfplumber
- pillow
- pytesseract if useful
- the current official Gemini Python SDK if appropriate

Do not add large or exotic dependencies unless clearly necessary.

Testing:
Create minimal smoke tests that verify:
- form family detection
- schema creation
- adapter mapping behavior
- output artifact creation in a simplified run

Also run the smoke tests after implementation and fix obvious failures.

README.md requirements:
Explain:
- project purpose
- architecture
- how Gemini is used
- fallback behavior without Gemini
- supported input file types
- supported form families
- how to run
- how to extend with a new adapter
- known limitations
- privacy note recommending fictional/sample data for demos
- that the normalized JSON schema is fixed and not dynamically invented at runtime

Important scope control:
Keep the implementation practical.
Avoid enterprise-style over-abstraction.
Avoid dozens of tiny files.
Avoid fake generality.
This is a demoable university project, not a production SaaS.

After creating the project:
1. install dependencies
2. run the smoke tests
3. run the CLI at least once against:
   - form/meghatalmazas.docx with input_data/demo_case
   - form/csaladi_kedvezmeny.docx with input_data/demo_case
4. fix obvious issues
5. then return only concise final status

## Adjustments
- use the current official Gemini Python SDK: google-genai instead of google-generativeai
- add an explicit schema module for the fixed normalized JSON structure, default object creation, and validation
- ensure fill_report.json tracks source provenance and field conflicts deterministically
- keep the codebase compact; if needed, merge tiny modules instead of creating too many files
- do not let the Gemini model invent the normalized JSON structure at runtime; it must fill a predefined schema
