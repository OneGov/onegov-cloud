from __future__ import annotations

from onegov.onboarding.models import Assistant


from typing import Any


def test_assistant() -> None:

    class FooAssistant(Assistant):

        @Assistant.step()
        def first_step(self, request: object) -> dict[str, Any]:
            return {'step': 1}

        @Assistant.step()
        def second_step(self, request: object) -> dict[str, Any]:
            return {'step': 2}

        @Assistant.step()
        def third_step(self, request: object) -> dict[str, Any]:
            return {'step': 3}

    app: Any = None
    request: Any = None
    foo = FooAssistant(app, current_step_number=1)
    assert foo.current_step.handle_view(request, None) == {'step': 1}
    assert foo.progress == (1, 3)
    assert foo.is_first_step == True
    assert foo.is_last_step == False

    foo = FooAssistant(app, current_step_number=2)
    assert foo.current_step.handle_view(request, None) == {'step': 2}
    assert foo.progress == (2, 3)
    assert foo.is_first_step == False
    assert foo.is_last_step == False

    foo = FooAssistant(app, current_step_number=3)
    assert foo.current_step.handle_view(request, None) == {'step': 3}
    assert foo.progress == (3, 3)
    assert foo.is_first_step == False
    assert foo.is_last_step == True
