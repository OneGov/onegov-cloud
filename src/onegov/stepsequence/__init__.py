from onegov.stepsequence.core import (
    Step, StepSequenceRegistry, as_step_registry_id
)

step_sequences = StepSequenceRegistry() # noqa

__all__ = ['Step', 'step_sequences', 'as_step_registry_id']
