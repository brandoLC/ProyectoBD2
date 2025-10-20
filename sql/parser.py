import re
from . import ast

_ws = r"\s+"
_ws_opt = r"\s*"  # espacios opcionales
_str = r'"([^"]+)"|\'([^\']+)\''
_ident = r'[\w\s]+'  # Identificador que puede incluir espacios
_col = r'"[^"]+"|\'[^\']+\'|[\w\s]+'  # Columna con o sin comillas (sin grupos de captura)

# CREATE TABLE con soporte para USING index_type
CREATE = re.compile(rf"^CREATE{_ws}TABLE{_ws}(\w+){_ws_opt}\(([^\)]+)\){_ws_opt}KEY{_ws_opt}\((\w+)\){_ws_opt}$", re.I)
CREATE_USING = re.compile(rf"^CREATE{_ws}TABLE{_ws}(\w+){_ws}USING{_ws}(\w+){_ws_opt}$", re.I)

# LOAD con soporte para FROM file
LOAD = re.compile(rf"^CREATE{_ws}TABLE{_ws}(\w+){_ws}FROM{_ws}FILE{_ws}({_str})$", re.I)
# LOAD FROM path INTO table - path puede ser string entre comillas o path simple
LOAD_FROM = re.compile(rf"^LOAD{_ws}FROM{_ws}([\w/. _-]+){_ws}INTO{_ws}(\w+){_ws_opt}$", re.I)

SELECT_EQ = re.compile(rf"^SELECT\s+\*\s+FROM{_ws}(\w+){_ws}WHERE{_ws}({_col}){_ws_opt}={_ws_opt}(.+)$", re.I)
SELECT_RANGE = re.compile(rf"^SELECT\s+\*\s+FROM{_ws}(\w+){_ws}WHERE{_ws}({_col}){_ws}BETWEEN{_ws}(.+){_ws}AND{_ws}(.+)$", re.I)
INSERT = re.compile(rf"^INSERT{_ws}INTO{_ws}(\w+){_ws_opt}\(([^\)]+)\){_ws_opt}VALUES{_ws_opt}\(([^\)]+)\){_ws_opt}$", re.I)
DELETE = re.compile(rf"^DELETE{_ws}FROM{_ws}(\w+){_ws}WHERE{_ws}({_col}){_ws_opt}={_ws_opt}(.+)$", re.I)


def _split_csv(s: str):
    return [x.strip() for x in s.split(",")]

def _clean_column_name(col: str) -> str:
    """Limpia nombre de columna (remueve comillas si existen)"""
    col = col.strip()
    if (col.startswith('"') and col.endswith('"')) or (col.startswith("'") and col.endswith("'")):
        return col[1:-1]
    return col


def parse(sql: str):
    s = sql.strip().rstrip(";")

    # CREATE TABLE name USING index_type
    m = CREATE_USING.match(s)
    if m:
        name, index_type = m.groups()
        return ast.CreateTableUsing(name=name, index_type=index_type)

    # CREATE TABLE name (cols) KEY (key)
    m = CREATE.match(s)
    if m:
        name, cols, key = m.groups()
        columns = _split_csv(cols)
        return ast.CreateTable(name=name, key=key, columns=columns)

    # LOAD FROM 'file.csv' INTO table
    m = LOAD_FROM.match(s)
    if m:
        path, table = m.groups()
        path = path.strip("\"'")  # Limpiar comillas si existen
        return ast.LoadCSV(table=table, path=path)

    # CREATE TABLE name FROM FILE 'path' (legacy)
    m = LOAD.match(s)
    if m:
        table, path = m.groups()[0], m.groups()[1]
        path = path.strip("\"'")
        return ast.LoadCSV(table=table, path=path)

    m = SELECT_RANGE.match(s)
    if m:
        table, col, lo, hi = m.groups()
        col = _clean_column_name(col)
        return ast.SelectRange(table=table, column=col, lo=eval(lo), hi=eval(hi))

    m = SELECT_EQ.match(s)
    if m:
        table, col, val = m.groups()
        col = _clean_column_name(col)
        return ast.SelectEq(table=table, column=col, value=eval(val))

    m = INSERT.match(s)
    if m:
        table, cols, vals = m.groups()
        cols_v = _split_csv(cols)
        vals_v = [eval(v) for v in _split_csv(vals)]
        return ast.InsertRow(table=table, values=dict(zip(cols_v, vals_v)))

    m = DELETE.match(s)
    if m:
        table, col, val = m.groups()
        col = _clean_column_name(col)
        return ast.DeleteEq(table=table, column=col, value=eval(val))

    raise ValueError("SQL no soportado: " + sql)
