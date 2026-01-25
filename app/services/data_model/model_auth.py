from dataclasses import dataclass
from typing import Optional, Any, Dict


@dataclass
class Country:
    country_abbr: str
    country_flag: Optional[str]
    country_name: str
    country_code: Optional[str]

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> Optional["Country"]:
        required_fields = ["n", "c"]
        if not all(field in data and data[field] for field in required_fields):
            return None
        return cls(
            country_abbr=data.get("c"),
            country_flag=data.get("e"),
            country_name=data.get("n"),
            country_code=data.get("d"),
        )
