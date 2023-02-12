from cached_property import cached_property

from onegov.stepsequence import step_sequences


class StepBaseExtension:

    def get_step_sequence(self, position=None):
        step = self.registered_steps().get(
            position=position or self.step_position
        )
        return step and step_sequences.by_id(step.id)


class StepsModelExtension(StepBaseExtension):
    """ Can serve as Model Extension. However, if you need some
    translations, is better to register steps on layouts that have access to
    the model. """

    @property
    def step_position(self):
        """ Can be overwritten by the model and based on its attributes. """
        return None

    @classmethod
    def registered_steps(cls):
        return step_sequences.registry[cls.__name__]


class StepsLayoutExtension(StepBaseExtension):
    """
    For steps registered on layouts.
    """

    def __init__(self, *args, **kwargs):
        self.hide_steps = kwargs.pop('hide_steps', False)
        super().__init__(*args, **kwargs)

    @property
    def step_position(self):
        """ Can be overwritten by the model and based request params. """
        raise NotImplementedError

    @cached_property
    def registered_steps(self):
        return step_sequences.registry[self.__class__.__name__]

    def get_step_sequence(self, position=None):
        """ Retrieve the full step sequence for the current model.
        If the latter has multiple steps registered, you must provide
        the position or a ValueError gets raised.
        """
        if self.hide_steps is True:
            return []

        step = self.registered_steps.get(
            position=position or self.step_position)
        return step and step_sequences.by_id(step.id)
