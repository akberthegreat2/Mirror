CREATE TABLE IF NOT EXISTS mirror_jobs (
    job_id UUID PRIMARY KEY,
    kind TEXT NOT NULL,
    run_id UUID,
    pipeline_id TEXT,
    step_id TEXT,
    execution_class TEXT NOT NULL DEFAULT 'default',
    payload JSONB NOT NULL,
    state TEXT NOT NULL,
    worker_id TEXT,
    error TEXT,
    metadata JSONB NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL,
    claimed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    lease_expires_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS mirror_jobs_queue_idx ON mirror_jobs(state, execution_class, submitted_at, job_id);
CREATE INDEX IF NOT EXISTS mirror_jobs_lease_idx ON mirror_jobs(state, lease_expires_at);
CREATE TABLE IF NOT EXISTS mirror_worker_heartbeats (
    worker_id TEXT PRIMARY KEY,
    heartbeat_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS mirror_leases (
    job_id UUID PRIMARY KEY,
    worker_id TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS mirror_leases_expiry_idx ON mirror_leases(expires_at);
CREATE TABLE IF NOT EXISTS mirror_execution_runs (
    run_id UUID PRIMARY KEY,
    outcome TEXT NOT NULL,
    payload JSONB NOT NULL,
    worker_id TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    metadata JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS mirror_checkpoints (
    run_id UUID NOT NULL,
    step_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY(run_id, step_id)
);
CREATE INDEX IF NOT EXISTS mirror_checkpoints_latest_idx ON mirror_checkpoints(run_id, created_at DESC);
CREATE TABLE IF NOT EXISTS mirror_artifacts (
    key TEXT PRIMARY KEY,
    payload BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS mirror_dead_letters (
    run_id UUID PRIMARY KEY,
    pipeline_id TEXT NOT NULL,
    step_id TEXT,
    reason TEXT NOT NULL,
    original_inputs JSONB NOT NULL,
    policy_state JSONB NOT NULL,
    provenance JSONB NOT NULL,
    retry_count INTEGER NOT NULL,
    terminal_status TEXT NOT NULL,
    worker_id TEXT,
    lease_id TEXT,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS mirror_metadata (
    namespace TEXT NOT NULL,
    key TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY(namespace, key)
);
