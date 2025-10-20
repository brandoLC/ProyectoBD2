from fastapi import FastAPI
from pydantic import BaseModel
from sql import parser, planner, executor
import time

app = FastAPI(title="BD2 Mini DBMS API")

class QueryIn(BaseModel):
    sql: str

@app.get("/health")
async def health():
    return {"status": "ok", "tables": list(executor.catalog.tables.keys())}

@app.post("/query")
async def query(q: QueryIn):
    start_time = time.perf_counter()  # Alta precisión
    node = parser.parse(q.sql)
    plan = planner.plan(node)
    out = executor.execute(plan)
    exec_time_ms = (time.perf_counter() - start_time) * 1000
    
    # Agregar tiempo de ejecución al resultado
    out['execution_time_ms'] = round(exec_time_ms, 3)
    return out
