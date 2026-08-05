# Workers

Workers are the part of Mirror that actually run jobs.

## Core contract

Mirror treats workers as a contract, not as one fixed implementation.

The core ideas are:

- submit a job;
- claim a job;
- checkpoint progress;
- finish or fail a job;
- resume later if needed.

## Alpha setup

The repository uses a local worker path for development and tests.

That keeps the project easy to run on a laptop while the beta backend work is still being built.
