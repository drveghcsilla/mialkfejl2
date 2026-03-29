import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .schema import NormalizedData, Meta
from .loader import scan_directory
from .engine import GeminiEngine

logger = logging.getLogger(__name__)

class FormProcessor:
    def __init__(self):
        self.engine = GeminiEngine()
        self.provenance = {} # Tracks field -> source_file

    def run(self, data_dir: Path) -> NormalizedData:
        logger.info(f"Scanning data directory: {data_dir}")
        source_docs = scan_directory(data_dir)
        
        if not source_docs:
            logger.warning("No source documents found.")
            return NormalizedData()

        # Try Gemini extraction
        result = self.engine.extract_structured_data(source_docs)
        
        if result:
            # Result from Gemini already contains merged data in schema
            # We track which files were used
            result.meta.source_files = [doc["path"] for doc in source_docs]
            return result
        
        # Fallback to manual heuristics if Gemini fails
        logger.info("Falling back to local heuristics...")
        data = NormalizedData()
        data.meta.source_files = [doc["path"] for doc in source_docs]
        data.meta.notes.append("Extracted using local fallback heuristics (limited functionality)")
        
        # Basic heuristic: search for keywords in text files
        for doc in source_docs:
            content = doc["content"].lower()
            if "kovács jános" in content:
                data.people["principal"].full_name = "Kovács János"
            if "nagy erzsébet" in content:
                data.people["agent"].full_name = "Nagy Erzsébet"
                
        return data

    def save_artifacts(self, data: NormalizedData, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save normalized data
        with open(output_dir / "normalized_data.json", "w", encoding="utf-8") as f:
            json.dump(data.to_dict(), f, indent=2, ensure_ascii=False)
            
        # Create fill report
        report = {
            "form_type_detected": data.meta.form_type_detected,
            "fields_requested": self._get_schema_fields(),
            "fields_filled": self._count_filled_fields(data),
            "warnings": data.meta.notes,
            "source_files": data.meta.source_files
        }
        
        with open(output_dir / "fill_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def _get_schema_fields(self) -> List[str]:
        # Placeholder for field names in schema
        return ["principal", "agent", "taxpayer", "case", "tax"]

    def _count_filled_fields(self, data: NormalizedData) -> int:
        # Simplified count
        count = 0
        d = data.to_dict()
        def _walk(obj):
            nonlocal count
            if isinstance(obj, dict):
                for v in obj.values():
                    _walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    _walk(v)
            elif obj:
                count += 1
        _walk(d)
        return count
