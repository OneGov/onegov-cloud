from __future__ import annotations

from functools import cached_property

from onegov.stepsequence import step_sequences


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.stepsequence.core import Step, StepCollection


class StepsModelExtension:
    """ Can serve as Model Extension. However, if you need some
    translations, is better to register steps on layouts that have access to
    the model. """

    @property
    def step_position(self) -> int | None:
        """ Can be overwritten by the model and based on its attributes. """
        return None

    def get_step_sequence(
        self,
        position: int | None = None
    ) -> list[Step]:
        step = self.registered_steps().get(
            position=position or self.step_position
        )
        return step and step_sequences.by_id(step.id) or []

    @classmethod
    def registered_steps(cls) -> StepCollection:
        return step_sequences.registry[cls.__name__]


class StepsLayoutExtension:
    """
    For steps registered on layouts.
    """

    def __init__(self, *args: Any, hide_steps: bool = False, **kwargs: Any):
        self.hide_steps = hide_steps
        super().__init__(*args, **kwargs)

    @property
    def step_position(self) -> int | None:
        """ Can be overwritten by the model and based request params. """
        raise NotImplementedError

    @cached_property
    def registered_steps(self) -> StepCollection:
        return step_sequences.registry[self.__class__.__name__]

    def get_step_sequence(
        self,
        position: int | None = None
    ) -> list[Step]:
        """ Retrieve the full step sequence for the current model.
        If the latter has multiple steps registered, you must provide
        the position or a ValueError gets raised.
        """
        if self.hide_steps is True:
            return []

        step = self.registered_steps.get(
            position=position or self.step_position)
        return step and step_sequences.by_id(step.id) or []
