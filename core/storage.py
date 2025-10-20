from typing import Any, Dict, List
from .io_metrics import IOMetrics

class Storage:
    """Almacenamiento simple en memoria con contador de I/O por páginas.
    Simula páginas mediante un factor de registros por página.
    """
    def __init__(self, records_per_page: int = 128) -> None:
        self._tables: Dict[str, List[Dict[str, Any]]] = {}
        self.metrics = IOMetrics()
        self.rpp = records_per_page

    def create_table(self, name: str) -> None:
        self._tables.setdefault(name, [])

    def load(self, name: str, rows: List[Dict[str, Any]]) -> None:
        self.create_table(name)
        self._tables[name].extend(rows)
        # simular writes por páginas
        pages = max(1, len(rows) // self.rpp + (1 if len(rows) % self.rpp else 0))
        self.metrics.write(pages)

    def read_all(self, name: str) -> List[Dict[str, Any]]:
        rows = self._tables.get(name, [])
        pages = max(1, len(rows) // self.rpp + (1 if len(rows) % self.rpp else 0))
        self.metrics.read(pages)
        return list(rows)
