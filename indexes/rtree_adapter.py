from typing import Any, Dict, List, Tuple
try:
    from rtree import index as rindex
    HAS_RTREE = True
except Exception:
    HAS_RTREE = False

class RTreeAdapter:
    """Adapter simple para (lat, lon) -> id y búsqueda por rango/k-NN."""
    def __init__(self) -> None:
        self.idx = rindex.Index() if HAS_RTREE else None
        self.rows: Dict[int, Dict[str, Any]] = {}
        self._id = 0

    def add(self, row: Dict[str, Any], lat: float, lon: float) -> None:
        self._id += 1
        rid = self._id
        self.rows[rid] = row
        if self.idx:
            self.idx.insert(rid, (lon, lat, lon, lat))  # bbox punto

    def range(self, lat: float, lon: float, radius: float) -> List[Dict[str, Any]]:
        if not self.idx:
            return []
        # aproximación bbox (círculo ≈ cuadrado):
        res = []
        for rid in self.idx.intersection((lon-radius, lat-radius, lon+radius, lat+radius)):
            res.append(self.rows[rid])
        return res

    def knn(self, lat: float, lon: float, k: int = 5) -> List[Dict[str, Any]]:
        if not self.idx:
            return []
        ids = list(self.idx.nearest((lon, lat, lon, lat), k))
        return [self.rows[i] for i in ids]
