import pytest

from onegov.stepsequence import Step, step_sequences
from onegov.stepsequence.extension import StepsModelExtension, \
    StepsLayoutExtension


def test_step():

    with pytest.raises(AssertionError):
        Step('1', 'ClassName', 2, cls_after='something')

    with pytest.raises(AssertionError):
        Step('1', 'ClassName', 1, cls_before='Nonsense')

    step = Step('1', 'Test', 1, cls_after='Test2')
    step2 = Step('1', 'Test2', 2, cls_before='Test')

    step_follow = Step('2', 'TestNext', 2, cls_before='Test')

    assert step2 > step
    assert step < step2
    assert step_follow > step
    assert step < step_follow

    step_ahead = Step('3', 'TestNext', 3, cls_before='Test')
    assert not step_ahead > step
    assert not step < step_ahead


def test_step_layout_extension(sequences):

    class BaseLayout(object):

        def __init__(self, model):
            self.model = model

    @sequences.registered_step(1, 'Start', cls_after='MiddleLayout')
    class StartLayout(BaseLayout, StepsLayoutExtension):
        @property
        def step_position(self):
            return 1

    @sequences.registered_step(2, 'Middle', cls_after='MiddleLayout', cls_before='StartLayout')
    class MiddleLayout(BaseLayout, StepsLayoutExtension):
        @property
        def step_position(self):
            return 2

    @sequences.registered_step(3, 'End', cls_before='MiddleLayout')
    class EndLayout(BaseLayout, StepsLayoutExtension):
        @property
        def step_position(self):
            return 3

    start = StartLayout(None)
    middle = MiddleLayout(None)
    end = EndLayout(None)

    assert start.get_step_sequence() == end.get_step_sequence() == \
           middle.get_step_sequence()


def test_step_registry(sequences):

    @sequences.registered_step(1, cls_after='Step2')
    class Step1(StepsModelExtension):
        pass

    @sequences.registered_step(2, cls_after='Step3', cls_before='Step1')
    class Step2(StepsModelExtension):
        pass

    @sequences.registered_step(3, cls_before='Step2')
    class Step3(StepsModelExtension):
        pass

    step1 = Step1.registered_steps().get(1)
    step2 = Step2.registered_steps().get(2)
    step3 = Step3.registered_steps().get(3)

    assert step1
    assert step2
    assert step3

    assert step1 < step2 < step3

    step = sequences.register('Extended', 2, cls_before='Nonsense')
    with pytest.raises(ValueError):
        sequences.by_id(step.id)

    # Functions are as well possible
    @sequences.registered_step(1, cls_after='other')
    def func(*args):
        return

    assert 'func' in sequences.registry


def test_step_registry_edge_cases(sequences):

    @sequences.registered_step(1)
    class MyClass(object):
        pass

    step = sequences.get(cls_name='MyClass')
    assert step == sequences.get(step_id=step.id)
    assert step.title == '1'

    assert not step_sequences.by_id(None)
    with pytest.raises(KeyError):
        step_sequences.by_id('BS')

    with pytest.raises(NotImplementedError):
        step_sequences.get()

    @sequences.registered_step(1, cls_after='MyClass')
    @sequences.registered_step(3, 'Return Start', cls_before='MyClass')
    class OtherClass(object):
        pass

    with pytest.raises(ValueError):
        sequences.get(cls_name='OtherClass')

    step = sequences.get(cls_name='OtherClass', position=1)
    assert step
    assert not sequences.get(cls_name='OtherClass', position=2)
    assert sequences.get(cls_name='OtherClass', position=3)

    # The step on MyClass is not defined..., the chain breaks after the first
    with pytest.raises(ValueError):
        sequences.by_id(step.id)

    # cls_before must be defined as well to not break the sequence
    with pytest.raises(AssertionError):
        sequences.register('MyClass', 2, cls_after='OtherClass')

    sequences.register(
        'MyClass', 2, cls_after='OtherClass', cls_before='OtherClass')
    steps = sequences.by_id(step.id)
    assert [s.origin for s in steps] == ['OtherClass', 'MyClass', 'OtherClass']

    step2 = steps[1]
    assert sequences.by_id(step2.id) == steps
