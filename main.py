import argparse
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from app.processor import FormProcessor
from app.filler import FormFiller
from app.loader import load_docx

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("output/run.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="DOCX Form Filling Agent")
    parser.add_argument("--form", required=True, help="Path to the DOCX form template")
    parser.add_argument("--data", required=True, help="Path to the input data folder")
    parser.add_argument("--output", required=True, help="Path to the output folder")
    
    args = parser.parse_args()
    
    form_path = Path(args.form)
    data_path = Path(args.data)
    output_path = Path(args.output)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting process for form: {form_path}")
    
    processor = FormProcessor()
    filler = FormFiller()
    
    # 1. Detect form type
    form_type = filler.detect_type(form_path)
    logger.info(f"Detected form type: {form_type}")
    
    # 2. Extract and normalize data
    data = processor.run(data_path)
    data.meta.form_type_detected = form_type
    
    # 3. Fill the form
    output_docx = output_path / f"filled_{form_path.name}"
    filler.fill(form_path, data, output_docx)
    
    # 4. Save artifacts
    processor.save_artifacts(data, output_path)
    
    logger.info("Process completed successfully.")

if __name__ == "__main__":
    main()
