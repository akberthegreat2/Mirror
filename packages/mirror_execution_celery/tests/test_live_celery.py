from __future__ import annotations

import os

import pytest


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("MIRROR_TEST_REDIS_URL"),
    reason="set MIRROR_TEST_REDIS_URL for live Redis/Celery integration",
)
def test_real_celery_worker_executes_through_redis() -> None:
    from celery import Celery
    from celery.contrib.testing.worker import start_worker

    broker = os.environ["MIRROR_TEST_REDIS_URL"]
    app = Celery("mirror-live", broker=broker)
    app.conf.update(
        task_ignore_result=False, result_backend=broker, worker_prefetch_multiplier=1
    )

    @app.task(name="mirror.live_smoke")
    def live_smoke(value: str) -> str:
        return f"ok:{value}"

    with start_worker(
        app, perform_ping_check=False, concurrency=1, pool="solo", loglevel="WARNING"
    ):
        result = live_smoke.delay("redis")
        assert result.get(timeout=15) == "ok:redis"
