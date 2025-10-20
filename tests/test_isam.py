import pytest
from indexes.isam import ISAMIndex


def test_isam_basic():
    """Test básico de ISAM: construcción, búsqueda e inserción"""
    idx = ISAMIndex(key="id", fanout=4)  # Fanout pequeño para testing
    
    # Datos iniciales
    data = [
        {"id": 10, "name": "A"},
        {"id": 5, "name": "B"},
        {"id": 15, "name": "C"},
        {"id": 20, "name": "D"},
        {"id": 25, "name": "E"},
        {"id": 30, "name": "F"},
        {"id": 12, "name": "G"},
        {"id": 8, "name": "H"},
    ]
    
    # Construir índice
    idx.build(data)
    
    # Verificar que se construyó correctamente
    stats = idx.stats()
    assert stats["num_buckets"] == 2  # 8 registros / 4 fanout = 2 buckets
    assert stats["records_in_buckets"] == 8
    
    # Test búsqueda por igualdad
    result = idx.search(10)
    assert len(result) == 1
    assert result[0]["name"] == "A"
    
    # Test búsqueda inexistente
    result = idx.search(999)
    assert len(result) == 0


def test_isam_range():
    """Test de búsqueda por rango"""
    idx = ISAMIndex(key="id", fanout=3)
    
    data = [{"id": i, "name": f"Item{i}"} for i in range(1, 21)]
    idx.build(data)
    
    # Búsqueda de rango
    result = idx.range_search(5, 10)
    ids = sorted([r["id"] for r in result])
    assert ids == [5, 6, 7, 8, 9, 10]
    
    # Rango grande
    result = idx.range_search(1, 20)
    assert len(result) == 20


def test_isam_overflow():
    """Test de inserciones con overflow"""
    idx = ISAMIndex(key="id", fanout=3)
    
    # Construir con datos iniciales
    data = [{"id": i, "name": f"Item{i}"} for i in [1, 2, 3, 10, 11, 12]]
    idx.build(data)
    
    stats_before = idx.stats()
    assert stats_before["records_in_overflow"] == 0
    
    # Insertar nuevos registros (van a overflow)
    idx.add({"id": 5, "name": "New5"})
    idx.add({"id": 15, "name": "New15"})
    
    stats_after = idx.stats()
    assert stats_after["records_in_overflow"] == 2
    assert stats_after["total_records"] == 8
    
    # Verificar que se pueden buscar
    result = idx.search(5)
    assert len(result) == 1
    assert result[0]["name"] == "New5"
    
    # Verificar rango incluyendo overflow
    result = idx.range_search(1, 20)
    assert len(result) == 8


def test_isam_delete():
    """Test de eliminación"""
    idx = ISAMIndex(key="id", fanout=4)
    
    data = [{"id": i, "name": f"Item{i}"} for i in range(1, 11)]
    idx.build(data)
    
    # Eliminar un registro
    deleted = idx.remove(5)
    assert deleted == 1
    
    # Verificar que ya no existe
    result = idx.search(5)
    assert len(result) == 0
    
    # Verificar que otros siguen existiendo
    result = idx.search(6)
    assert len(result) == 1


def test_isam_vs_sequential():
    """Comparación conceptual entre ISAM y Sequential"""
    from indexes.sequential import SequentialIndex
    
    # Crear datos de prueba
    data = [{"id": i, "name": f"Item{i}"} for i in range(1, 101)]
    
    # ISAM
    isam = ISAMIndex(key="id", fanout=10)
    isam.build(data)
    
    # Sequential
    seq = SequentialIndex(key="id")
    for r in data:
        seq.add(r)
    
    # Ambos deben encontrar lo mismo
    isam_result = isam.search(50)
    seq_result = seq.search(50)
    
    assert len(isam_result) == 1
    assert len(seq_result) == 1
    assert isam_result[0]["id"] == seq_result[0]["id"]
    
    # Rango
    isam_range = isam.range_search(40, 60)
    seq_range = seq.range_search(40, 60)
    
    assert len(isam_range) == len(seq_range) == 21


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
