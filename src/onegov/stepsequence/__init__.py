from __future__ import annotations

from onegov.stepsequence.core import (
    Step, StepSequenceRegistry, as_step_registry_id
)

# FIXME: A single shared registry kind of goes against the spirit of
#        morepath. We should consider switching to a directive with
#        a unique registry per App.
step_sequences = StepSequenceRegistry()

__all__ = ('Step', 'step_sequences', 'as_step_registry_id')
