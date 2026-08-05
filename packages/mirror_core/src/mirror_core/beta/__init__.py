"""Pre-beta staging area for functionality not covered by the alpha contract.

Everything under ``mirror_core.beta`` is real, tested code that previews
work described in ``docs/BETA_CONTRACT.md`` (metadata storage, blob storage,
recurring-schedule persistence). None of it is part of the frozen alpha
guarantees in ``docs/ALPHA_CONTRACT.md``, none of it is wired into
``Application``, and none of it is covered by ``docs/ARCHITECTURE.md``
§4's subsystem table.

Rules for anything living in this subpackage:

- It MAY change shape, move to its own package, or be deleted without
  following the deprecation process the rest of Mirror Core follows.
- It MUST NOT be imported by any non-beta module in ``mirror_core``.
- It MUST be moved out of ``mirror_core`` entirely (into its own
  capability/provider package pair, consistent with the rest of the
  workspace's packaging pattern) before it is promoted out of beta status,
  rather than being un-marked in place.

Importing this subpackage emits a ``FutureWarning`` so that any accidental
production dependency on it is loud rather than silent.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "mirror_core.beta is a pre-beta staging area, not covered by the "
    "frozen alpha contract (see docs/ALPHA_CONTRACT.md and "
    "docs/BETA_CONTRACT.md). Its contents may change or move without "
    "the deprecation process the rest of mirror_core follows.",
    FutureWarning,
    stacklevel=2,
)