from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class CreateTable:
    name: str
    key: str
    columns: List[str]

@dataclass
class CreateTableUsing:
    name: str
    index_type: str

@dataclass
class LoadCSV:
    table: str
    path: str

@dataclass
class SelectEq:
    table: str
    column: str
    value: Any

@dataclass
class SelectRange:
    table: str
    column: str
    lo: Any
    hi: Any

@dataclass
class InsertRow:
    table: str
    values: Dict[str, Any]

@dataclass
class DeleteEq:
    table: str
    column: str
    value: Any
