from __future__ import annotations

from typing import overload, Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable

_F = TypeVar('_F', bound='Callable[..., Any]')


class DuplicatedStepError(Exception):
    pass


def as_step_registry_id(
    cls_name: str,
    position: int,
    cls_before: str | None = None,
    cls_after: str | None = None
) -> str:
    return ':'.join((
        str(position),
        cls_name,
        cls_before or '',
        cls_after or ''
    ))


class Step:

    def __init__(
        self,
        title: int | str,
        origin: str,
        position: int,
        cls_after: str | None = None,
        cls_before: str | None = None
    ):

        assert isinstance(position, int)
        if cls_before:
            assert isinstance(cls_before, str)
            assert position > 1, 'Subsequent steps can not start at 1'
        else:
            assert position == 1, 'Starting steps must begin with position 1'
        if cls_after:
            assert isinstance(cls_after, str)

        self.title = title if not isinstance(title, int) else str(title)
        self.position = position
        self.origin = origin
        self.cls_after = cls_after
        self.cls_before = cls_before

    def __lt__(self, other: Step) -> bool:
        return (
            other.cls_before == self.origin
            and other.position - 1 == self.position
        )

    def __gt__(self, other: Step) -> bool:
        return (
            self.cls_before == other.origin
            and self.position - 1 == other.position
        )

    @property
    def id(self) -> str:
        """Unique ID for a step. """
        return as_step_registry_id(
            self.origin, self.position, self.cls_before, self.cls_after
        )

    def __repr__(self) -> str:
        return (
            f'Step({self.position}, {self.title!s}, '
            f'cls_after={self.cls_after}, cls_before={self.cls_before})'
        )


class StepCollection:

    _steps: list[Step]

    def __init__(self) -> None:
        self._steps = []

    def _ids(self) -> set[str]:
        return {s.id for s in self._steps}

    def add(self, step: Step) -> None:
        if step.id in self._ids():
            raise DuplicatedStepError
        self._steps.append(step)

    def keys(self) -> set[str]:
        return self._ids()

    def get(self, position: int | None = None) -> Step | None:
        if position:
            steps = tuple(s for s in self._steps if s.position == position)
            return steps and steps[0] or None
        if len(self._steps) == 1:
            return self._steps[0]
        raise ValueError(
            'Multiple sequences match your class name specify position')


class StepSequenceRegistry:

    registry: dict[str, StepCollection]
    flattened_registry: dict[str, Step]

    def __init__(self) -> None:
        self.registry = {}
        self.flattened_registry = {}

    def get(
        self,
        step_id: str | None = None,
        cls_name: str | None = None,
        position: int | None = None
    ) -> Step | None:
        if step_id:
            return self.flattened_registry[step_id]
        if cls_name:
            return self.registry[cls_name].get(position)
        raise NotImplementedError

    @overload
    def by_id(self, step_id: str) -> list[Step]: ...
    @overload
    def by_id(self, step_id: None) -> None: ...

    def by_id(self, step_id: str | None) -> list[Step] | None:
        if step_id is None:
            return None

        step = self.flattened_registry[step_id]
        steps = []
        prev_step = step
        while prev_step.cls_before:
            found = False
            for s in self.flattened_registry.values():
                if s < prev_step:
                    steps.append(s)
                    prev_step = s
                    found = True
                    break
            if not found:
                raise ValueError(
                    f'{prev_step.cls_before} with number '
                    f'{prev_step.position - 1} not registered'
                )

        steps.reverse()
        steps.append(step)

        next_step = step
        while next_step.cls_after:
            found = False
            for s in self.flattened_registry.values():
                if s > next_step:
                    steps.append(s)
                    next_step = s
                    found = True
                    break
            if not found:
                raise ValueError(
                    f'{next_step.cls_after} with number '
                    f'{next_step.position + 1} not registered'
                )

        return steps

    def register(
        self,
        cls_name: str,
        position: int,
        title: str | None = None,
        cls_before: str | None = None,
        cls_after: str | None = None
    ) -> Step:
        """ Registers a step by its position, and the class names that come
        before and after. """

        step = Step(
            title=title or str(position),
            origin=cls_name,
            position=position,
            cls_after=cls_after,
            cls_before=cls_before
        )
        cls_entry = self.registry.setdefault(cls_name, StepCollection())
        cls_entry.add(step)
        self.flattened_registry[step.id] = step
        return step

    def registered_step(
        self,
        position: int,
        title: str | None = None,
        cls_before: str | None = None,
        cls_after: str | None = None
    ) -> Callable[[_F], _F]:

        """ A decorator to register part of a full step sequence.

        Use as follows::

            @step_sequences.registered_step(
            1, _('Confirm'), cls_after='FormSubmission')
            class MyDBModel(Base, StepsExtension):
                pass

        """
        def wrapper(model_class: _F) -> _F:
            self.register(
                title=title,
                position=position,
                cls_name=model_class.__name__,
                cls_before=cls_before,
                cls_after=cls_after
            )
            return model_class
        return wrapper
