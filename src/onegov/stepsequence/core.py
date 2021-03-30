
class DuplicatedStepError(Exception):
    pass


def as_step_registry_id(cls_name, position, cls_before=None, cls_after=None):
    return ':'.join((
        str(position),
        cls_name,
        cls_before or '',
        cls_after or ''
    ))


class Step(object):

    def __init__(
            self, title, origin, position, cls_after=None, cls_before=None):

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

    def __lt__(self, other):
        return other.cls_before == self.origin \
            and other.position - 1 == self.position

    def __gt__(self, other):
        return self.cls_before == other.origin \
            and self.position - 1 == other.position

    @property
    def id(self):
        """Unique ID for a step. """
        return as_step_registry_id(
            self.origin, self.position, self.cls_before, self.cls_after
        )

    def __repr__(self):
        return f'Step({self.position}, {str(self.title)}, ' \
               f'cls_after={self.cls_after}, cls_before={self.cls_before})'


class StepCollection:

    def __init__(self):
        self._steps = []

    def _ids(self):
        return {s.id for s in self._steps}

    def add(self, step):
        if step.id in self._ids():
            raise DuplicatedStepError
        self._steps.append(step)

    def keys(self):
        return self._ids()

    def get(self, position=None):
        if position:
            steps = tuple(s for s in self._steps if s.position == position)
            return steps and steps[0]
        if len(self._steps) == 1:
            return self._steps[0]
        raise ValueError(
            'Multiple sequences match your class name specify position')


class StepSequenceRegistry(object):

    def __init__(self):
        self.registry = {}
        self.flattened_registry = {}

    def get(self, step_id=None, cls_name=None, position=None):
        if step_id:
            return self.flattened_registry[step_id]
        if cls_name:
            return self.registry[cls_name].get(position)
        raise NotImplementedError

    def by_id(self, step_id):
        if not step_id:
            return
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

        steps = list(reversed(steps))
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
            self, cls_name, position, title=None, cls_before=None,
            cls_after=None
    ):
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
            self, position, title=None, cls_before=None, cls_after=None):

        """ A decorator to register part of a full step sequence as follows::

        @step_sequences.registered_step(
        1, _('Confirm'), cls_after='FormSubmission')
        class MyDBModel(Base, StepsExtension):
            pass

        """
        def wrapper(model_class):
            self.register(
                title=title,
                position=position,
                cls_name=model_class.__name__,
                cls_before=cls_before,
                cls_after=cls_after
            )
            return model_class
        return wrapper
