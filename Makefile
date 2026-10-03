.PHONY: install test run ui lint

install:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev,ui]"

lint:
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

test: lint
	.venv/bin/pytest

run:
	.venv/bin/uvicorn app.main:app --reload --port 8000

ui:
	.venv/bin/streamlit run streamlit_app/app.py
