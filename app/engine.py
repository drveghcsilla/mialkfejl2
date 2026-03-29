import os
import json
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from .schema import NormalizedData

logger = logging.getLogger(__name__)

class GeminiEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found. Fallback mode will be active.")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
            self.model_id = "gemini-3.1-flash-lite-preview"

    def extract_structured_data(self, source_docs: List[Dict[str, Any]]) -> Optional[NormalizedData]:
        if not self.client:
            return None

        # Build multimodal parts
        parts = []
        instructions = "Extract information from the provided documents and images into a unified JSON schema.\n"
        instructions += "If a document is an image (like an ID card), extract all person details (name, birth info, mother's name, ID number).\n"
        instructions += "Look for city and date (e.g., 'Kelt: Budapest, 2026. március 29.') and place them in case.city and case.date.\n"
        instructions += "Check for Tax ID numbers (8-10 digits) and submission year.\n"
        instructions += "Schema structure:\n"
        instructions += """
        {
          "people": {
            "principal": { "full_name": "", "birth_place": "", "birth_date": "", "mother_name": "", "id_number": "", "address": "", "tax_id": "" },
            "agent": { ... },
            "witness_1": { "full_name": "", "address": "", "id_number": "" },
            "witness_2": { "full_name": "", "address": "", "id_number": "" },
            "taxpayer": { "full_name": "", "tax_id": "" },
            "partner": { "full_name": "", "tax_id": "" }
          },
          "case": { "authority_name": "", "case_type": "", "city": "", "date": "" },
          "tax": { "submission_year": "", "joint_claim": false, "dependents": [{"name": "", "tax_id": ""}] }
        }
        """
        parts.append(instructions)

        for i, doc in enumerate(source_docs):
            header = f"\n--- SOURCE {i} ({doc['path']}) ---\n"
            if doc["content_type"] == "text":
                parts.append(f"{header}\n{doc['content']}\n")
            elif doc["content_type"] == "image":
                parts.append(header)
                parts.append(types.Part.from_bytes(data=doc["content"], mime_type=doc["mime"]))

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=parts,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
            if response.text:
                logger.info(f"Gemini returned response ({len(response.text)} bytes). Parsing...")
                data_dict = json.loads(response.text)
                return NormalizedData.from_dict(data_dict)
            return None
        except Exception as e:
            logger.error(f"Gemini multimodal extraction failed: {e}")
            return None

    def analyze_form_type(self, form_content: str) -> str:
        if not self.client:
            return "unknown"
            
        prompt = f"""
        Identify the type of the following document.
        Possible types: "power_of_attorney" or "family_tax_benefit".
        Return ONLY the type identifier string.
        
        DOCUMENT CONTENT:
        {form_content}
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            return response.text.strip().lower()
        except:
            return "unknown"
