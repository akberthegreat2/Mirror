# Validation Record

Validated on Python 3.13 in the review environment.

- `pytest`: **86 passed, 2 skipped**. The skipped tests require `warcio`, which is not installed in the test interpreter.
- All nine package wheels built successfully with `pip wheel --no-deps --no-build-isolation`.
- Wheels installed together into an isolated virtual environment with `--no-deps`.
- Imports resolved from the installed virtual-environment `site-packages`, not repository source paths.
- Installed entry points exposed capabilities, providers, middleware, and CLI descriptors.
- Installed `mirror --help` completed successfully.
- `python -m compileall` completed successfully.

Ruff and mypy could not be installed from the environment's package index, so those two commands must still run in project CI before tagging.
