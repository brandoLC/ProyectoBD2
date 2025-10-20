from dataclasses import dataclass
from typing import List

@dataclass
class Column:
    name: str
    type: str  # "INT", "FLOAT", "TEXT", etc.

@dataclass
class TableSchema:
    name: str
    columns: List[Column]
    key: str  # columna clave primaria
