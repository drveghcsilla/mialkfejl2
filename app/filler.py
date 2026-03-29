import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from docx import Document
from .schema import NormalizedData

logger = logging.getLogger(__name__)

class FormAdapter:
    @staticmethod
    def get_concept_labels(form_type: str) -> Dict[str, List[str]]:
        if form_type == "power_of_attorney":
            return {
                "people.principal.full_name": ["alulírott", "én,", "név:"],
                "people.principal.address": ["lakóhely:", "lakcím:"],
                "people.principal.id_number": ["személyazonosító igazolványának száma:", "szem. ig. szám.:"],
                "people.principal.mother_name": ["anyja neve:"],
                "people.principal.birth_date": ["születési hely, idő:"],
                "people.agent.full_name": ["meghatalmazom"],
                "people.agent.address": ["lakcím:"],
                "people.agent.id_number": ["személyazonosító igazolványának száma:"],
                "people.agent.mother_name": ["anyja neve:"],
                "people.agent.birth_date": ["születési hely, idő:"],
                "case.authority_name": ["(eljáró hatóság megnevezése)", "hatóság megnevezése"],
                "case.case_type": ["(ügy típusának megjelölése)", "ügy típusának megjelölése"],
                "case.city": ["kelt:"],
                "case.date": ["év", "hónap", "nap"],
                "people.witness_1.full_name": ["név:"],
                "people.witness_1.address": ["lakcím:"],
                "people.witness_1.id_number": ["szem. ig. szám.:"],
                "people.witness_2.full_name": ["név:"],
                "people.witness_2.address": ["lakcím:"],
                "people.witness_2.id_number": ["szem. ig. szám.:"],
            }
        elif form_type == "family_tax_benefit":
            return {
                "tax.submission_year": ["benyújtásának éve:"],
                "people.taxpayer.full_name": ["magánszemély neve:"],
                "people.taxpayer.tax_id": ["adóazonosító jele:"],
                "tax.joint_claim": ["együtt érvényesítjük", "közös érvényesítés"],
                "tax.is_modified": ["módosító nyilatkozat"],
                "tax.dependents.name": ["név"],
                "tax.dependents.tax_id": ["adóazonosító jel"],
                "tax.dependents.em_code": ["em*"],
                "tax.dependents.jj_code": ["jj**"],
                "tax.dependents.change_date": ["változás időpontja"],
            }
        return {}

class FormFiller:
    def __init__(self):
        self.current_section = None
        self.current_dep_idx = 0

    def detect_type(self, doc_path: Path) -> str:
        try:
            doc = Document(doc_path)
            ft = "\n".join([p.text for p in doc.paragraphs]).lower()
            if "meghatalmazás" in ft: return "power_of_attorney"
            if "családi" in ft or "nyilatkozat" in ft: return "family_tax_benefit"
            return "unknown"
        except: return "unknown"

    def fill(self, template_path: Path, data: NormalizedData, output_path: Path):
        form_type = data.meta.form_type_detected
        labels_map = FormAdapter.get_concept_labels(form_type)
        doc = Document(template_path)
        self.current_section = None
        self.current_dep_idx = 0
        
        # Process all paragraphs, including those in tables if any
        paragraphs = []
        for p in doc.paragraphs: paragraphs.append(p)
        for t in doc.tables:
            for r in t.rows:
                for c in r.cells:
                    for p in c.paragraphs: paragraphs.append(p)
        
        for p in paragraphs:
            self._fill_p(p, labels_map, data)
        
        doc.save(output_path)
        logger.info(f"Saved filled DOCX to {output_path}")

    def _fill_p(self, paragraph, labels_map, data):
        text = paragraph.text
        if not text.strip(): return
        t_low = text.lower()
        
        # Section detection
        if "tanú 1.:" in t_low: self.current_section = "witness_1"
        elif "tanú 2.:" in t_low: self.current_section = "witness_2"
        elif "meghatalmazom" in t_low: self.current_section = "agent"
        elif "én," in t_low or "alulírott" in t_low: self.current_section = "principal"
        elif "kelt:" in t_low: self.current_section = "signature"
        elif any(k in t_low for k in ["adóazonosító jel", "eltartottak"]) or "⎕⎕⎕⎕⎕⎕" in text:
             self.current_section = "tax_details"

        original_text = text
        person_prefix = f"people.{self.current_section}." if self.current_section and self.current_section not in ["tax_details", "signature"] else ""
        P_RE = r"([\.…_\-]{3,}|⎕+)"

        if text.strip().startswith(('.', '…')) and self.current_section == "agent":
             val = self._get_data_value(data, "people.agent.full_name")
             if val: text = re.sub(r"^[\s\.…_\-]{3,}", f" {val} ", text)

        filled_any = False; used_ids = set()
        while True:
            changed = False
            ms = list(re.finditer(P_RE, text))
            if not ms: break
            
            # POSITIONAL DATE LINE
            if self.current_section == "signature" and "év" in t_low and len(ms) >= 3:
                 v_city = self._get_data_value(data, "case.city")
                 v_year = self._get_data_value(data, "case.date", "év")
                 v_mo = self._get_data_value(data, "case.date", "hónap")
                 v_day = self._get_data_value(data, "case.date", "nap")
                 vals = [v_city, v_year, v_mo, v_day]
                 nt = text
                 for v in vals:
                       curr_ms = list(re.finditer(P_RE, nt))
                       if curr_ms and v:
                            m = curr_ms[0]
                            nt = nt[:m.start()] + f" {v} " + nt[m.end():]
                 text = nt; filled_any = True; break

            # POSITIONAL DEPENDENT ROW
            if self.current_section == "tax_details" and ("⎕⎕⎕⎕⎕⎕" in text or "jj**" in t_low) and len(ms) >= 2:
                 tid = self._get_data_value(data, "tax.dependents.tax_id")
                 nm = self._get_data_value(data, "tax.dependents.name")
                 if tid or nm:
                      nt = text
                      mg = list(re.finditer(r"⎕{8,12}", nt))
                      if mg and tid: nt = nt[:mg[0].start()] + self._get_formatted_val(tid, mg[0].group(0)) + nt[mg[0].end():]
                      md = list(re.finditer(r"[\.…]{5,}", nt))
                      if md and nm: nt = nt[:md[0].start()] + f" {nm} " + nt[md[0].end():]
                      text = nt; filled_any = True; break

            # Scored fallback
            scores = []
            for m in ms:
                ph = m.group(1); ps, pe = m.start(), m.end()
                if any(c not in "⎕.…_- " for c in ph): continue 
                for path, lbls in labels_map.items():
                    if person_prefix and path.startswith("people.") and not path.startswith(person_prefix): continue
                    if "tax.dependents" in path: continue
                    for lbl in lbls:
                        l_id = f"{path}|{lbl}"
                        if l_id in used_ids: continue
                        for lm in re.finditer(re.escape(lbl), text, re.IGNORECASE):
                            d = 999
                            if lm.end() <= ps: d = ps - lm.end()
                            elif lm.start() >= pe: d = lm.start() - pe
                            else: continue
                            if d < 40:
                                b = text[min(lm.end(), pe):max(lm.start(), ps)]
                                if not re.search(r"[\.…_]{3,}", b):
                                    scores.append({"score": d, "m": m, "path": path, "label": lbl, "id": l_id})
            
            scores.sort(key=lambda x: x["score"])
            if scores:
                best = scores[0]; val = self._get_data_value(data, best["path"], context_label=best["label"])
                if val is not None:
                    text = text[:best["m"].start()] + self._get_formatted_val(val, best["m"].group(1)) + text[best["m"].end():]
                    used_ids.add(best["id"]); changed = True; filled_any = True
            if not changed: break

        # Tabbed signature block
        if self.current_section == "signature" and "\t" in text:
             pv, av = self._get_data_value(data, "people.principal.full_name"), self._get_data_value(data, "people.agent.full_name")
             if pv or av:
                  parts = text.split("\t"); nps = []
                  for p in parts:
                       if re.search(r"[\.…]{3,}", p):
                            if pv and not any(str(pv) in s for s in nps): nps.append(f" {pv} ")
                            elif av and not any(str(av) in s for s in nps): nps.append(f" {av} ")
                            else: nps.append(p)
                       else: nps.append(p)
                  text = "\t".join(nps); filled_any = True

        if filled_any and self.current_section == "tax_details" and ("⎕⎕⎕⎕⎕⎕" in text or "jj**" in t_low):
             self.current_dep_idx += 1
        if text != original_text: paragraph.text = text

    def _get_formatted_val(self, val: Any, placeholder: str) -> str:
        if isinstance(val, bool):
             if "⎕" in placeholder: return " X " if val else "   "
             return "[X]" if val else "[ ]"
        sv = str(val); res = []; idx = 0
        if "⎕" in placeholder:
             for c in placeholder:
                  if c == "⎕": res.append(sv[idx] if idx < len(sv) else " "); idx += 1
                  else: res.append(c)
             return "".join(res)
        return f" {sv} "

    def _get_data_value(self, data: NormalizedData, path: str, context_label: str = "") -> Any:
        try:
            pts = path.split('.'); obj = data
            for pt in pts:
                if pt == "dependents" and isinstance(obj, list):
                     if self.current_dep_idx < len(obj): obj = obj[self.current_dep_idx]
                     else: return None
                else: obj = obj.get(pt) if isinstance(obj, dict) else getattr(obj, pt)
            if "birth_date" in path:
                pl = self._get_data_value_raw(data, path.replace("birth_date", "birth_place"))
                return f"{pl}, {obj}" if pl and obj else (obj or pl)
            if path == "case.date" and context_label:
                ds = str(obj); m = re.search(r"(\d{4})[\.\s]+([^\s\.]+?)[\.\s]+(\d{1,2})", ds)
                if m:
                    if "év" in context_label: return m.group(1)
                    if "hónap" in context_label: return m.group(2)
                    if "nap" in context_label: return m.group(3)
                p = ds.split('.')
                if "év" in context_label: return p[0].strip() if len(p)>0 else ""
                if "hónap" in context_label: return p[1].strip().split(' ')[0] if len(p)>1 else ""
                if "nap" in context_label: 
                     if len(p)>1 and ' ' in p[1].strip(): return p[1].strip().split(' ')[1]
                     return p[2].strip() if len(p)>2 else ""
            return obj
        except: return None

    def _get_data_value_raw(self, data: NormalizedData, path: str) -> Any:
        try:
            pts = path.split('.'); obj = data
            for pt in pts: obj = obj.get(pt) if isinstance(obj, dict) else getattr(obj, pt)
            return obj
        except: return None
