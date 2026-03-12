from __future__ import annotations

import inspect
import time


from typing import overload, Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.request import CoreRequest
    from onegov.form import Form
    from onegov.onboarding.app import OnboardingApp
    from typing import Self, TypeAlias

    _T = TypeVar('_T')
    _F = TypeVar('_F', bound='Callable[..., Any]')
    _ViewF = TypeVar('_ViewF', bound='Callable[[Any, CoreRequest], Any]')
    _FormT = TypeVar('_FormT', bound='Form')
    _FormView: TypeAlias = Callable[[Any, CoreRequest, _FormT], _T]


class Assistant:
    """ Describes an assistant guiding a user through onboarding. """

    def __init__(self, app: OnboardingApp, current_step_number: int = 1):

        self.app = app

        methods = (fn[1] for fn in inspect.getmembers(self))
        methods = (fn for fn in methods if inspect.ismethod(fn))
        methods = (fn for fn in methods if hasattr(fn, 'is_step'))

        self.steps = sorted(Step(fn, fn.order, fn.form) for fn in methods)

        if current_step_number < 1:
            raise KeyError('Invalid current step')

        if current_step_number > len(self.steps):
            raise KeyError('Invalid current step')

        self.current_step_number = current_step_number

    @property
    def current_step(self) -> Step:
        return self.steps[self.current_step_number - 1]

    @property
    def progress(self) -> tuple[int, int]:
        return self.current_step_number, len(self.steps)

    @property
    def is_first_step(self) -> bool:
        return self.current_step_number == 1

    @property
    def is_last_step(self) -> bool:
        return self.current_step_number == len(self.steps)

    def for_next_step(self) -> Self:
        assert not self.is_last_step
        return self.__class__(self.app, self.current_step_number + 1)

    def for_prev_step(self) -> Self:
        assert not self.is_first_step
        return self.__class__(self.app, self.current_step_number - 1)

    def for_first_step(self) -> Self:
        return self.__class__(self.app, 1)

    @overload
    @classmethod
    def step(cls, form: None = None) -> Callable[[_ViewF], _ViewF]: ...

    @overload
    @classmethod
    def step(
        cls,
        form: type[_FormT]
    ) -> Callable[[_FormView[_FormT, _T]], _FormView[_FormT, _T]]: ...

    @classmethod
    def step(cls, form: type[Form] | None = None) -> Callable[[_F], _F]:
        def decorator(fn: _F) -> _F:
            fn.is_step = True  # type:ignore[attr-defined]
            # FIXME: monotonic may be more reliable
            fn.order = time.process_time()  # type:ignore[attr-defined]
            fn.form = form  # type:ignore[attr-defined]

            return fn

        return decorator


class Step:
    """ Describes a step in an assistant. """

    @overload
    def __init__(
        self,
        view_handler: Callable[[CoreRequest], Any],
        order: float,
        form: None
    ): ...

    @overload
    def __init__(
        self,
        view_handler: Callable[[CoreRequest, Form], Any],
        order: float,
        form: Form
    ): ...

    def __init__(
        self,
        view_handler: Callable[..., Any],
        order: float,
        form: Form | None
    ):
        self.view_handler = view_handler
        self.order = order
        self.form = form

    def __lt__(self, other: Step) -> bool:
        return self.order < other.order

    def handle_view(self, request: CoreRequest, form: Form | None) -> Any:
        if form is None:
            return self.view_handler(request)
        else:
            return self.view_handler(request, form)


class DefaultAssistant:
    def __init__(self, assistant: Assistant):
        self.assistant = assistant
