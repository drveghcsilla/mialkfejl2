import unittest
from pathlib import Path
from app.schema import NormalizedData
from app.filler import FormFiller, FormAdapter
from app.processor import FormProcessor

class TestFormAgent(unittest.TestCase):
    def test_schema_serialization(self):
        data = NormalizedData()
        data.people["principal"].full_name = "Test User"
        d = data.to_dict()
        self.assertEqual(d["people"]["principal"]["full_name"], "Test User")
        
        data2 = NormalizedData.from_dict(d)
        self.assertEqual(data2.people["principal"].full_name, "Test User")

    def test_form_detection(self):
        filler = FormFiller()
        # Mock detection or check real files if exists
        p = Path("form/meghatalmazas.docx")
        if p.exists():
            t = filler.detect_type(p)
            self.assertEqual(t, "power_of_attorney")

    def test_adapter_mapping(self):
        m = FormAdapter.get_mapping("power_of_attorney")
        self.assertIn("PRINCIPAL_NAME", m)
        self.assertEqual(m["PRINCIPAL_NAME"], "people.principal.full_name")

if __name__ == "__main__":
    unittest.main()
