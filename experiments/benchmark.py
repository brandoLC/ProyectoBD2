import time
import requests
import csv

API = "http://localhost:8000"

def run(sql: str):
    t0 = time.perf_counter()
    out = requests.post(f"{API}/query", json={"sql": sql}).json()
    dt = (time.perf_counter() - t0) * 1000
    return out, dt

if __name__ == "__main__":
    rows = []
    for val in [10, 100, 1000, 5000]:
        out, ms = run(f"SELECT * FROM Restaurantes WHERE id = {val}")
        rows.append({"val": val, "ms": ms, "count": out.get("count", 0), **out.get("io", {})})
    with open("experiments/results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print("OK -> experiments/results.csv")
