from onegov.stepsequence.core import (
    Step, StepSequenceRegistry, as_step_registry_id
)

step_sequences = StepSequenceRegistry()

__all__ = ('Step', 'step_sequences', 'as_step_registry_id')
