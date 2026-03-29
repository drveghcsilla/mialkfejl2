import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from PIL import Image
import pytesseract
from pypdf import PdfReader
from docx import Document

logger = logging.getLogger(__name__)

def load_text(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Failed to read text file {file_path}: {e}")
        return ""

def load_docx(file_path: Path) -> str:
    try:
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        logger.warning(f"Failed to read docx file {file_path}: {e}")
        return ""

def load_pdf(file_path: Path) -> str:
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.warning(f"Failed to read pdf file {file_path}: {e}")
        return ""

def load_image_bytes(file_path: Path) -> bytes:
    try:
        return file_path.read_bytes()
    except Exception as e:
        logger.warning(f"Failed to read image bytes for {file_path}: {e}")
        return b""

def scan_directory(directory: Path) -> List[Dict[str, Any]]:
    results = []
    for root, _, files in os.walk(directory):
        for file in files:
            path = Path(root) / file
            if not path.is_file(): continue
            
            ext = path.suffix.lower()
            content_type = "text"
            content = None
            mime = "text/plain"

            if ext in [".txt", ".md"]:
                content = load_text(path)
                mime = "text/plain"
            elif ext == ".json":
                content = load_text(path)
                mime = "application/json"
            elif ext == ".docx":
                content = load_docx(path)
                mime = "text/plain"
            elif ext == ".pdf":
                # For PDF, we can either extract text OR send bytes for Gemini OCR
                content = load_pdf(path)
                mime = "text/plain"
            elif ext in [".png", ".jpg", ".jpeg"]:
                content = load_image_bytes(path)
                content_type = "image"
                mime = f"image/{ext[1:] if ext != '.jpg' else 'jpeg'}"
            
            if content:
                results.append({
                    "path": str(path),
                    "filename": file,
                    "content": content,
                    "content_type": content_type,
                    "mime": mime
                })
    return results
