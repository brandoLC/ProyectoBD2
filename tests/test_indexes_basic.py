import pytest
from indexes.sequential import SequentialIndex


def test_sequential_basic():
    idx = SequentialIndex(key="id")
    data = [
        {"id": 2, "name": "B"},
        {"id": 1, "name": "A"},
        {"id": 3, "name": "C"},
    ]
    for r in data:
        idx.add(r)
    # igualdad
    assert idx.search(1) == [{"id": 1, "name": "A"}]
    # rango
    res = idx.range_search(1, 2)
    assert [r["id"] for r in res] == [1, 2]
