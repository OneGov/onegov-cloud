import inspect
import time


class Assistant(object):
    """ Describes an assistant guiding a user through onboarding. """

    def __init__(self, app, current_step_number=1):

        self.app = app

        methods = (fn[1] for fn in inspect.getmembers(self))
        methods = (fn for fn in methods if inspect.ismethod(fn))
        methods = (fn for fn in methods if hasattr(fn, 'is_step'))

        self.steps = [Step(fn, fn.order, fn.form) for fn in methods]
        self.steps.sort()

        if current_step_number < 1:
            raise KeyError("Invalid current step")

        if current_step_number > len(self.steps):
            raise KeyError("Invalid current step")

        self.current_step_number = current_step_number

    @property
    def current_step(self):
        return self.steps[self.current_step_number - 1]

    @property
    def progress(self):
        return self.current_step_number, len(self.steps)

    @property
    def is_first_step(self):
        return self.current_step_number == 1

    @property
    def is_last_step(self):
        return self.current_step_number == len(self.steps)

    def for_next_step(self):
        assert not self.is_last_step
        return self.__class__(self.app, self.current_step_number + 1)

    def for_prev_step(self):
        assert not self.is_first_step
        return self.__class__(self.app, self.current_step_number - 1)

    def for_first_step(self):
        return self.__class__(self.app, 1)

    @classmethod
    def step(cls, form=None):
        def decorator(fn):
            fn.is_step = True
            fn.order = time.process_time()
            fn.form = form

            return fn

        return decorator


class Step(object):
    """ Describes a step in an assistant. """

    def __init__(self, view_handler, order, form):
        self.view_handler = view_handler
        self.order = order
        self.form = form

    def __lt__(self, other):
        return self.order < other.order

    def handle_view(self, request, form):
        if form is None:
            return self.view_handler(request)
        else:
            return self.view_handler(request, form)


class DefaultAssistant(object):
    def __init__(self, assistant):
        self.assistant = assistant
