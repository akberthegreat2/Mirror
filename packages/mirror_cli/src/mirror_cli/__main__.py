"""Module entry point for ``python -m mirror_cli``."""

from __future__ import annotations

from mirror_cli.main import app


def main() -> None:
    """Run the Mirror CLI application."""
    app()


if __name__ == "__main__":
    main()
