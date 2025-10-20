from typing import Any, Dict, List
from . import ast
from core.schema import Column, TableSchema
from core.table import Table
from core.disk_storage import DiskStorage
from core.utils import load_csv

class Catalog:
    def __init__(self) -> None:
        self.storage = DiskStorage(data_dir="storage")
        self.tables: Dict[str, Table] = {}
        # Restaurar tablas desde disco
        self._restore_tables()
    
    def _restore_tables(self) -> None:
        """Restaura tablas desde el catálogo persistido"""
        for table_name in self.storage.list_tables():
            metadata = self.storage.get_table_metadata(table_name)
            if metadata and metadata.get("schema"):
                # Reconstruir schema
                schema_data = metadata["schema"]
                columns = [Column(col["name"], col["type"]) for col in schema_data["columns"]]
                schema = TableSchema(
                    name=schema_data["name"],
                    key=schema_data["key"],
                    columns=columns
                )
                # Crear tabla con el índice especificado y reconstruir índices
                index_type = metadata.get("index_type", "sequential")
                self.tables[table_name] = Table(
                    schema=schema, 
                    storage=self.storage, 
                    index_type=index_type,
                    rebuild_indexes=True  # Reconstruir índices desde disco
                )

    def ensure(self, name: str, key: str, columns: List[str]) -> Table:
        if name not in self.tables:
            schema = TableSchema(name=name, key=key, columns=[Column(c, "TEXT") for c in columns])
            self.storage.create_table(name)
            self.tables[name] = Table(schema=schema, storage=self.storage)
        return self.tables[name]

catalog = Catalog()


def execute(node: Any) -> Dict[str, Any]:
    if isinstance(node, ast.CreateTable):
        t = catalog.ensure(node.name, node.key, node.columns)
        return {"ok": True, "table": t.name}
    
    if isinstance(node, ast.CreateTableUsing):
        # Crear tabla con tipo de índice especificado
        if node.name not in catalog.tables:
            # Guardar el tipo de índice en metadata
            catalog.storage.set_table_metadata(node.name, index_type=node.index_type)
        return {"ok": True, "table": node.name, "index_type": node.index_type}

    if isinstance(node, ast.LoadCSV):
        rows = load_csv(node.path)
        # inferir key como primera columna si no existe tabla
        if node.table not in catalog.tables:
            key = list(rows[0].keys())[0]
            
            # Obtener el tipo de índice desde metadata
            metadata = catalog.storage.get_table_metadata(node.table)
            index_type = metadata.get("index_type", "sequential") if metadata else "sequential"
            
            # Crear schema (nota: orden correcto es name, columns, key)
            columns_list = [Column(c, "TEXT") for c in rows[0].keys()]
            schema = TableSchema(name=node.table, columns=columns_list, key=key)
            
            # Guardar schema en metadata
            schema_dict = {
                "name": schema.name,
                "key": schema.key,
                "columns": [{"name": col.name, "type": col.type} for col in schema.columns]
            }
            catalog.storage.set_table_metadata(node.table, schema=schema_dict, index_type=index_type)
            
            # Crear tabla con el índice apropiado
            catalog.tables[node.table] = Table(schema=schema, storage=catalog.storage, index_type=index_type)
        
        t = catalog.tables[node.table]
        
        # Resetear métricas de los índices antes de LOAD
        for idx in t.indexes.values():
            if hasattr(idx, 'reset_io_stats'):
                idx.reset_io_stats()
        
        t.load(rows)
        
        # Obtener estadísticas de I/O de los índices después de BUILD
        io_stats = {'disk_reads': 0, 'disk_writes': 0}
        for idx in t.indexes.values():
            if hasattr(idx, 'get_io_stats'):
                index_io = idx.get_io_stats()
                io_stats['disk_reads'] += index_io.get('disk_reads', 0)
                io_stats['disk_writes'] += index_io.get('disk_writes', 0)
        
        return {"ok": True, "loaded": len(rows), "io_stats": io_stats}

    if isinstance(node, ast.InsertRow):
        t = catalog.tables[node.table]
        
        # Limpiar métricas antes del INSERT
        catalog.storage.metrics.disk_reads = 0
        catalog.storage.metrics.disk_writes = 0
        
        # Resetear métricas de los índices
        for idx in t.indexes.values():
            if hasattr(idx, 'reset_io_stats'):
                idx.reset_io_stats()
        
        t.insert(node.values)
        
        # Obtener estadísticas de I/O de los índices
        io_stats = {'disk_reads': 0, 'disk_writes': 0}
        for idx in t.indexes.values():
            if hasattr(idx, 'get_io_stats'):
                index_io = idx.get_io_stats()
                io_stats['disk_reads'] += index_io.get('disk_reads', 0)
                io_stats['disk_writes'] += index_io.get('disk_writes', 0)
        
        # Sumar I/O del storage (si hubo)
        io_stats['disk_reads'] += catalog.storage.metrics.disk_reads
        io_stats['disk_writes'] += catalog.storage.metrics.disk_writes
        
        return {"ok": True, "inserted": 1, "io": io_stats}

    if isinstance(node, ast.DeleteEq):
        t = catalog.tables[node.table]
        
        # Resetear métricas del índice antes de DELETE
        idx = t.get_index(node.column)
        if idx and hasattr(idx, 'reset_io_stats'):
            idx.reset_io_stats()
        
        # Ejecutar DELETE
        n = t.delete(node.value)
        
        # Obtener estadísticas de I/O del índice
        io_stats = {'disk_reads': 0, 'disk_writes': 0}
        if idx and hasattr(idx, 'get_io_stats'):
            index_io = idx.get_io_stats()
            io_stats['disk_reads'] += index_io.get('disk_reads', 0)
            io_stats['disk_writes'] += index_io.get('disk_writes', 0)
        
        return {
            "ok": True, 
            "deleted": n,
            "io_stats": io_stats
        }

    if isinstance(node, ast.SelectEq):
        t = catalog.tables[node.table]
        
        # Limpiar métricas de storage antes de la query
        catalog.storage.metrics.disk_reads = 0
        catalog.storage.metrics.disk_writes = 0
        
        # Resetear métricas del índice
        idx = t.get_index(node.column)
        if idx and hasattr(idx, 'reset_io_stats'):
            idx.reset_io_stats()
        
        rows = t.select_eq(node.column, node.value)
        
        # Obtener estadísticas de I/O del índice
        io_stats = {'disk_reads': 0, 'disk_writes': 0}
        if idx and hasattr(idx, 'get_io_stats'):
            index_io = idx.get_io_stats()
            io_stats['disk_reads'] += index_io.get('disk_reads', 0)
            io_stats['disk_writes'] += index_io.get('disk_writes', 0)
        
        # Sumar I/O del storage (si hubo)
        io_stats['disk_reads'] += catalog.storage.metrics.disk_reads
        io_stats['disk_writes'] += catalog.storage.metrics.disk_writes
        
        return {"rows": rows, "count": len(rows), "io": io_stats}

    if isinstance(node, ast.SelectRange):
        t = catalog.tables[node.table]
        
        # Limpiar métricas de storage antes de la query
        catalog.storage.metrics.disk_reads = 0
        catalog.storage.metrics.disk_writes = 0
        
        # Resetear métricas del índice
        idx = t.get_index(node.column)
        if idx and hasattr(idx, 'reset_io_stats'):
            idx.reset_io_stats()
        
        rows = t.select_range(node.column, node.lo, node.hi)
        
        # Obtener estadísticas de I/O del índice
        io_stats = {'disk_reads': 0, 'disk_writes': 0}
        if idx and hasattr(idx, 'get_io_stats'):
            index_io = idx.get_io_stats()
            io_stats['disk_reads'] += index_io.get('disk_reads', 0)
            io_stats['disk_writes'] += index_io.get('disk_writes', 0)
        
        # Sumar I/O del storage (si hubo)
        io_stats['disk_reads'] += catalog.storage.metrics.disk_reads
        io_stats['disk_writes'] += catalog.storage.metrics.disk_writes
        
        return {"rows": rows, "count": len(rows), "io": io_stats}

    raise ValueError("Nodo no soportado")
