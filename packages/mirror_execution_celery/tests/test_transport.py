from __future__ import annotations

import os

import pytest

from mirror_execution_celery.transport import create_celery_app, queue_name


def test_execution_class_queue_names() -> None:
    assert queue_name("default") == "mirror.default"
    assert queue_name("io") == "mirror.io"
    assert queue_name("CPU") == "mirror.cpu"
    with pytest.raises(ValueError):
        queue_name("crawl.queue")


def test_celery_app_uses_redis_broker() -> None:
    app = create_celery_app(broker_url="redis://localhost:6399/0")
    assert app.conf.broker_url == "redis://localhost:6399/0"
    assert app.conf.task_acks_late is True
    assert app.conf.worker_prefetch_multiplier == 1
    assert app.conf.task_ignore_result is True


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("MIRROR_TEST_REDIS_URL"),
    reason="set MIRROR_TEST_REDIS_URL for live Redis/Celery integration",
)
def test_live_redis_url_is_configurable() -> None:
    from redis import Redis

    url = os.environ["MIRROR_TEST_REDIS_URL"]
    client = Redis.from_url(url)
    assert client.ping() is True
