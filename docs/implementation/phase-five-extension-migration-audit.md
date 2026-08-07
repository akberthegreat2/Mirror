# Extension migration audit

Status: Planned

Mirror currently carries a legacy registry language alongside the canonical manifest extension model.

The beta gate for that migration is to:
- identify every package still using the legacy registry API as a primary path;
- determine whether each usage is a compatibility shim or a true dependency;
- move shipped capability/provider packages onto the canonical extension path where required;
- keep the user-facing documentation honest while the migration is in progress.

This is a documentation and validation phase, not a new runtime feature.
