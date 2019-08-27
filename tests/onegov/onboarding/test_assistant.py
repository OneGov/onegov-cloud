from onegov.onboarding.models import Assistant


def test_assistant():

    class FooAssistant(Assistant):

        @Assistant.step()
        def first_step(self, request):
            return {'step': 1}

        @Assistant.step()
        def second_step(self, request):
            return {'step': 2}

        @Assistant.step()
        def third_step(self, request):
            return {'step': 3}

    foo = FooAssistant(None, current_step_number=1)
    assert foo.current_step.handle_view(None, None) == {'step': 1}
    assert foo.progress == (1, 3)
    assert foo.is_first_step == True
    assert foo.is_last_step == False

    foo = FooAssistant(None, current_step_number=2)
    assert foo.current_step.handle_view(None, None) == {'step': 2}
    assert foo.progress == (2, 3)
    assert foo.is_first_step == False
    assert foo.is_last_step == False

    foo = FooAssistant(None, current_step_number=3)
    assert foo.current_step.handle_view(None, None) == {'step': 3}
    assert foo.progress == (3, 3)
    assert foo.is_first_step == False
    assert foo.is_last_step == True
