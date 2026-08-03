"""Signal definitions for the Fetch capability."""

# Signal names for the Fetch capability
SIGNAL_FETCH_STARTED = "fetch.started"
SIGNAL_FETCH_SUCCEEDED = "fetch.succeeded"
SIGNAL_FETCH_FAILED = "fetch.failed"
SIGNAL_FETCH_RETRYING = "fetch.retrying"

# All signals exported as a list for registration
signals = [
    SIGNAL_FETCH_STARTED,
    SIGNAL_FETCH_SUCCEEDED,
    SIGNAL_FETCH_FAILED,
    SIGNAL_FETCH_RETRYING,
]
