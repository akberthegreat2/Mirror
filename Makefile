.PHONY: install type lint format test clean

install:
	@for pkg in packages/*/; do \
		echo "Installing $$pkg"; \
		pip install -e "$$pkg"; \
	done

type:
	@echo "=== Running type checks ==="
	@for pkg in packages/*/; do \
		if [ -d "$$pkg/src" ]; then \
			echo "Checking $$pkg"; \
			(cd "$$pkg" && mypy src) || exit 1; \
		fi; \
	done

lint:
	@echo "=== Running lints ==="
	ruff check packages/

format:
	ruff format packages/

test:
	@echo "=== Running tests ==="
	@pytest packages/*/tests

clean:
	@echo "=== Cleaning ==="
	find packages -type d -name "*.egg-info" -exec rm -rf {} +
	find packages -type d -name "__pycache__" -exec rm -rf {} +
	find packages -type d -name ".pytest_cache" -exec rm -rf {} +
	find packages -type d -name ".mypy_cache" -exec rm -rf {} +

check:
	@echo "=== Linting ==="
	ruff check packages/
	@echo "=== Formatting ==="
	ruff format packages/
	@echo "=== Type checking ==="
	make type

check: lint format type test
	@echo "=== All checks passed ==="
