# ADR-0002: Pipelines Are Directed Acyclic Graphs (DAGs)

## Status
Accepted

## Context
Early designs of Mirror used a simple ordered list of steps (e.g., `["fetch", "archive"]`). This is insufficient for real-world workflows that require branching, parallelism, conditions, and dependencies (e.g., fetch multiple URLs then archive only successful ones).

## Decision
Pipelines are defined as a Directed Acyclic Graph (DAG) of steps. Each step declares its inputs (dependencies on other steps or pipeline inputs) and outputs. The planner validates the graph, detects cycles, and produces an execution order with parallel groups.

## Consequences
- Execution can be parallelized automatically.
- Dependencies are explicit and verifiable.
- Cycle detection prevents infinite loops.
- Pipelines become declarative and reusable.
- Type checking across step boundaries becomes possible via port definitions.

## Alternatives Considered
- **Ordered list**: Too restrictive; cannot express branching or parallelism.
- **Custom script language**: Too complex; would reinvent DAG semantics.
- **Argo/Airflow-style DAG**: Too heavy; we only need a subset.

## Decision Rationale
DAGs are a proven model for data pipelines and provide the necessary expressive power while keeping execution deterministic and verifiable.
