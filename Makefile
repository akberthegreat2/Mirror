.PHONY: install lint format format-check type test wheels clean check

install:
	@for pkg in packages/*/; do \
		if [ -f "$$pkg/pyproject.toml" ]; then \
			echo "Installing $$pkg"; \
			python -m pip install -e "$$pkg" || exit 1; \
		fi; \
	done

lint:
	ruff check .

format:
	ruff format .

format-check:
	ruff format --check .

type:
	@for pkg in packages/*/; do \
		if [ -d "$$pkg/src" ]; then \
			echo "Checking $$pkg"; \
			(cd "$$pkg" && mypy src) || exit 1; \
		fi; \
	done

test:
	pytest

wheels: clean
	@mkdir -p dist
	@for pkg in packages/*/; do \
		if [ -f "$$pkg/pyproject.toml" ]; then \
			python -m pip wheel --no-deps --no-build-isolation -w dist "$$pkg" || exit 1; \
		fi; \
	done

clean:
	find . -type d \( -name build -o -name dist -o -name "*.egg-info" -o -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache \) -prune -exec rm -rf {} +

check: lint format-check type test
	@echo "=== All checks passed ==="
