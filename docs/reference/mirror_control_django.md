# mirror-control-django (planned)

This page documents the proposed Django control-plane surface for Mirror. The
repository snapshot does **not** ship a `mirror_control_django` package yet.

The planned control-plane work is described in:

- ADR-0017 — Django control plane
- ADR-0020 — Django control-plane contract
- ADR-0021 — Control-plane metadata models
- ADR-0022 — Admin visibility and roles
- ADR-0023 — Optional Django dependency

## Intended responsibilities

- render a Django settings fragment for a future control-plane project;
- describe the metadata models the control plane will manage;
- keep Django out of `mirror_core`;
- remain optional until the control-plane package is actually added.

## Status

Planned. Not shipped in this snapshot.
