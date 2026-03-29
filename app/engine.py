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
        instructions = "Extract information from the provided documents and images into a unified JSON.\n"
        instructions += "If an image (like an ID card) and text files disagree on any field (e.g. principal ID number), pick the most likely correct one deterministically, but record the conflict explicitly in 'meta.conflicts' outlining the discrepancy.\n"
        instructions += "For Family Tax Benefit forms, dependents ONLY require: tax_id, name, em_code, jj_code, and change_date. Do NOT try to extract or place birth dates for dependents.\n"
        instructions += "Schema structure:\n"
        instructions += """
        {
          "meta": {
            "conflicts": []
          },
          "people": {
            "principal": { "full_name": "", "birth_place": "", "birth_date": "", "mother_name": "", "id_number": "", "address": "", "tax_id": "" },
            "agent": { "full_name": "", "id_number": "", "birth_date": "" },
            "witness_1": { "full_name": "", "address": "", "id_number": "" },
            "witness_2": { "full_name": "", "address": "", "id_number": "" },
            "taxpayer": { "full_name": "", "tax_id": "" },
            "partner": { "full_name": "", "tax_id": "" }
          },
          "case": { "authority_name": "", "case_type": "", "city": "", "date": "" },
          "tax": { "submission_year": "", "joint_claim": false, "hungary_only_claim": false, "disable_contribution_discount": false, "discount_amount_huf": "", "beneficiary_count": "", "employer_name": "", "employer_tax_number": "", "partner_employer_name": "", "partner_employer_tax_number": "", "dependents": [{"name": "", "tax_id": "", "em_code": "", "jj_code": "", "change_date": ""}] }
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
