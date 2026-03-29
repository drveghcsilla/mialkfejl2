from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

@dataclass
class Person:
    full_name: str = ""
    birth_place: str = ""
    birth_date: str = ""
    mother_name: str = ""
    id_number: str = ""
    address: str = ""
    tax_id: str = ""

@dataclass
class Witness:
    full_name: str = ""
    address: str = ""
    id_number: str = ""

@dataclass
class Case:
    authority_name: str = ""
    case_type: str = ""
    city: str = ""
    date: str = ""

@dataclass
class Dependent:
    tax_id: str = ""
    name: str = ""
    em_code: str = ""
    jj_code: str = ""
    change_date: str = ""

@dataclass
class Tax:
    submission_year: str = ""
    is_modified: bool = False
    joint_claim: bool = False
    hungary_only_claim: bool = True
    disable_contribution_discount: bool = False
    discount_amount_huf: str = ""
    beneficiary_count: str = ""
    employer_name: str = ""
    employer_tax_number: str = ""
    partner_employer_name: str = ""
    partner_employer_tax_number: str = ""
    dependents: List[Dependent] = field(default_factory=list)

@dataclass
class Meta:
    form_type_detected: str = ""
    source_files: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)

@dataclass
class NormalizedData:
    meta: Meta = field(default_factory=Meta)
    people: Dict[str, Person] = field(default_factory=lambda: {
        "principal": Person(),
        "agent": Person(),
        "taxpayer": Person(),
        "partner": Person(),
        "witness_1": Witness(),
        "witness_2": Witness()
    })
    case: Case = field(default_factory=Case)
    tax: Tax = field(default_factory=Tax)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedData":
        res = cls()
        if "meta" in data and isinstance(data["meta"], dict):
            res.meta = Meta(**{k: v for k, v in data["meta"].items() if k in Meta.__dataclass_fields__})
        if "people" in data and isinstance(data["people"], dict):
            for k, v in data["people"].items():
                if k in res.people and isinstance(v, dict):
                    if k in ["witness_1", "witness_2"]:
                        res.people[k] = Witness(**{k2: v2 for k2, v2 in v.items() if k2 in Witness.__dataclass_fields__})
                    else:
                        res.people[k] = Person(**{k2: v2 for k2, v2 in v.items() if k2 in Person.__dataclass_fields__})
        if "case" in data and isinstance(data["case"], dict):
            res.case = Case(**{k: v for k, v in data["case"].items() if k in Case.__dataclass_fields__})
        if "tax" in data and isinstance(data["tax"], dict):
            tax_data = data["tax"].copy()
            # Heuristic for common misnames
            if "year" in tax_data and "submission_year" not in tax_data:
                tax_data["submission_year"] = tax_data.pop("year")
            
            deps = tax_data.pop("dependents", [])
            valid_tax_data = {k: v for k, v in tax_data.items() if k in Tax.__dataclass_fields__ and v is not None}
            res.tax = Tax(**valid_tax_data)
            for d in deps:
                if isinstance(d, dict):
                    res.tax.dependents.append(Dependent(**{k: v for k, v in d.items() if k in Dependent.__dataclass_fields__ and v is not None}))
        return res
