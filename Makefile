.PHONY: install test lint index web clean

install:
	pip install -e ".[dev]"

test:
	pytest

web:
	streamlit run repomind/app.py

index:
	python -m repomind.cli index .

clean:
	rm -rf .vectorstore .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
