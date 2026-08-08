FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY packages /app/packages
COPY pyproject.toml README.md /app/

RUN python -m pip install --no-cache-dir \
        'pydantic>=2.0' 'pydantic-settings>=2.0' 'packaging>=23.0' \
        'celery>=5.6' 'redis>=6.2' 'psycopg>=3.2' 'tzlocal>=5.0' 'scrapy>=2.11' \
        && for pkg in packages/mirror_core packages/mirror_worker_postgres packages/mirror_execution_celery packages/mirror_fetch packages/mirror_crawl packages/mirror_crawl_scrapy; do \
             python -m pip install --no-cache-dir -e "$pkg"; \
           done

ENTRYPOINT ["mirror-celery-worker"]
