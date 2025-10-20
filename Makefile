.PHONY: api ui up down test

api:
	uvicorn api.main:app --reload --port 8000

ui:
	streamlit run ui/app.py --server.port 8501

up:
	docker compose up --build

down:
	docker compose down

test:
	pytest -q
