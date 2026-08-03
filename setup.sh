#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(pwd)"

# Create directory structure
mkdir -p packages/mirror-core/src/mirror_core
mkdir -p packages/mirror-core/tests
mkdir -p packages/mirror-fetch/src/mirror_fetch
mkdir -p packages/mirror-fetch/tests
mkdir -p packages/mirror-fetch-httpx/src/mirror_fetch_httpx
mkdir -p packages/mirror-fetch-httpx/tests
mkdir -p packages/mirror-testing/src/mirror_testing
mkdir -p packages/mirror-testing/tests
mkdir -p packages/mirror-cli/src/mirror_cli
mkdir -p packages/mirror-cli/tests

# Write root pyproject.toml (NO dependencies)
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mirror-workspace"
version = "0.1.0"
description = "Mirror application framework workspace"
readme = "README.md"
requires-python = ">=3.10"

[project.optional-dependencies]
dev = [
    "ruff>=0.3.0",
    "mypy>=1.8.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
]

[tool.ruff]
target-version = "py310"
line-length = 100
select = ["E", "W", "F", "I", "N", "UP", "B", "C4", "SIM", "T20"]
ignore = ["E501", "B008"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]
"**/__init__.py" = ["F401"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.10"
strict = true
ignore_missing_imports = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_configs = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["packages/*/tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"
addopts = "-v --strict-markers --tb=short"
markers = [
    "asyncio",
    "integration",
    "contract",
]
EOF

# Write mirror-core/pyproject.toml (core only, no capability deps)
cat > packages/mirror-core/pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mirror-core"
version = "0.1.0"
description = "Mirror core kernel – capability-agnostic chassis"
readme = "README.md"
license = {text = "MIT"}
authors = [{name = "Mirror Contributors"}]
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
]
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[project.optional-dependencies]
test = ["pytest>=7.0", "pytest-asyncio>=0.21", "pytest-cov>=4.0"]
dev = ["ruff>=0.1.0", "mypy>=1.0"]

[tool.setuptools.packages.find]
where = ["src"]
include = ["mirror_core*"]
namespaces = false

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
asyncio_mode = "auto"

[tool.mypy]
plugins = ["pydantic.mypy"]
EOF

# Write mirror-fetch/pyproject.toml (depends on core)
cat > packages/mirror-fetch/pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mirror-fetch"
version = "0.1.0"
description = "Mirror Fetch capability – retrieve web resources"
readme = "README.md"
license = {text = "MIT"}
authors = [{name = "Mirror Contributors"}]
requires-python = ">=3.10"
dependencies = [
    "mirror-core>=0.1.0",
    "pydantic>=2.0",
]
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[project.optional-dependencies]
test = ["pytest>=7.0", "pytest-asyncio>=0.21", "pytest-cov>=4.0"]
dev = ["ruff", "mypy"]

[project.entry-points."mirror"]
fetch = "mirror_fetch:capability"

[tool.setuptools.packages.find]
where = ["src"]
include = ["mirror_fetch*"]
namespaces = false

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
asyncio_mode = "auto"
EOF

# Write mirror-fetch-httpx/pyproject.toml (depends on core + fetch)
cat > packages/mirror-fetch-httpx/pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mirror-fetch-httpx"
version = "0.1.0"
description = "HTTPX provider for Mirror Fetch"
readme = "README.md"
license = {text = "MIT"}
authors = [{name = "Mirror Contributors"}]
requires-python = ">=3.10"
dependencies = [
    "mirror-core>=0.1.0",
    "mirror-fetch>=0.1.0",
    "httpx>=0.24",
]
classifiers = [
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[project.optional-dependencies]
test = ["pytest>=7.0", "pytest-asyncio>=0.21", "pytest-httpx>=0.30"]
dev = ["ruff", "mypy"]

[project.entry-points."mirror"]
httpx = "mirror_fetch_httpx:provider"

[tool.setuptools.packages.find]
where = ["src"]
include = ["mirror_fetch_httpx*"]
namespaces = false

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
asyncio_mode = "auto"
EOF

# Write mirror-testing/pyproject.toml
cat > packages/mirror-testing/pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mirror-testing"
version = "0.1.0"
description = "Shared contract-testing utilities for Mirror"
readme = "README.md"
license = {text = "MIT"}
authors = [{name = "Mirror Contributors"}]
requires-python = ">=3.10"
dependencies = [
    "mirror-core>=0.1.0",
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
]
classifiers = [
    "Programming Language :: Python :: 3",
]

[tool.setuptools.packages.find]
where = ["src"]
include = ["mirror_testing*"]
namespaces = false
EOF

# Write mirror-cli/pyproject.toml
cat > packages/mirror-cli/pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mirror-cli"
version = "0.1.0"
description = "Mirror CLI interface – dynamic command discovery"
readme = "README.md"
license = {text = "MIT"}
authors = [{name = "Mirror Contributors"}]
requires-python = ">=3.10"
dependencies = [
    "mirror-core>=0.1.0",
    "typer>=0.9",
]
classifiers = [
    "Programming Language :: Python :: 3",
]

[project.optional-dependencies]
test = ["pytest>=7.0", "pytest-asyncio>=0.21"]
dev = ["ruff", "mypy"]

[project.entry-points."mirror"]
cli = "mirror_cli:interface"

[tool.setuptools.packages.find]
where = ["src"]
include = ["mirror_cli*"]
namespaces = false

[project.scripts]
mirror = "mirror_cli.main:app"
EOF

# Create __init__.py files
touch packages/mirror-core/src/mirror_core/__init__.py
touch packages/mirror-fetch/src/mirror_fetch/__init__.py
touch packages/mirror-fetch-httpx/src/mirror_fetch_httpx/__init__.py
touch packages/mirror-testing/src/mirror_testing/__init__.py
touch packages/mirror-cli/src/mirror_cli/__init__.py

touch packages/mirror-core/tests/__init__.py
touch packages/mirror-fetch/tests/__init__.py
touch packages/mirror-fetch-httpx/tests/__init__.py
touch packages/mirror-testing/tests/__init__.py
touch packages/mirror-cli/tests/__init__.py

# Write README
cat > README.md << 'EOF'
# Mirror

Mirror is an application framework for building web infrastructure.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full specification.

## Development

```bash
# Install dev tools
pip install -e .[dev]

# Install packages individually
pip install -e packages/mirror-core
pip install -e packages/mirror-fetch
pip install -e packages/mirror-fetch-httpx

# Run all tests
pytest

# Lint and format
ruff check .
ruff format .

# Type check
mypy .
```
EOF

# Write .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
.venv/
venv/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
*.log
EOF

# Write Makefile
cat > Makefile << 'EOF'
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
EOF

echo "Bootstrap complete. Next steps:"
echo "  cd $REPO_ROOT"
echo "  pip install -e .[dev]"
echo "  pip install -e packages/mirror-core"
echo "  pip install -e packages/mirror-fetch"
echo "  pip install -e packages/mirror-fetch-httpx"
echo "  pytest"
echo "  ruff check ."
