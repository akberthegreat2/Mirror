.PHONY: install-dev test lint format typecheck clean

install-dev:
	pip install -e .[dev]

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy .

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache dist build *.egg-info
