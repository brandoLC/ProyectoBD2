import csv
from typing import Any, Dict, List

def _convert_value(value: str) -> Any:
    """Intenta convertir un string al tipo apropiado"""
    # Intentar convertir a int
    try:
        return int(value)
    except ValueError:
        pass
    
    # Intentar convertir a float
    try:
        return float(value)
    except ValueError:
        pass
    
    # Dejar como string
    return value

def load_csv(path: str) -> List[Dict[str, Any]]:
    """Carga CSV y convierte valores a tipos apropiados.
    Soporta UTF-8 (inglés y caracteres internacionales)."""
    
    try:
        # Intentar con UTF-8 estricto primero
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = []
            for row in reader:
                # Convertir cada valor al tipo apropiado
                converted_row = {k: _convert_value(v) for k, v in row.items()}
                rows.append(converted_row)
            
            print(f"✓ CSV cargado con UTF-8")
            return rows
    
    except (UnicodeDecodeError, UnicodeError):
        # Si UTF-8 falla, usar UTF-8 con reemplazo de caracteres inválidos
        print("⚠ Advertencia: Algunos caracteres no son UTF-8 válidos, usando reemplazo (� para caracteres corruptos)")
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            rows = []
            for row in reader:
                converted_row = {k: _convert_value(v) for k, v in row.items()}
                rows.append(converted_row)
            return rows
