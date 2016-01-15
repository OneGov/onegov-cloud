import inspect
import time


class Assistant(object):
    """ Describes an assistant guiding a user through onboarding. """

    def __init__(self):

        methods = (fn[1] for fn in inspect.getmembers(self))
        methods = (fn for fn in methods if inspect.ismethod(fn))
        methods = (fn for fn in methods if hasattr(fn, 'is_step'))

        self.steps = [Step(fn, fn.order) for fn in methods]
        self.steps.sort()

    @classmethod
    def step(cls, fn):
        fn.is_step = True
        fn.order = time.process_time()

        return fn


class Step(object):
    """ Describes a step in an assistant. """

    def __init__(self, view_handler, order):
        self.view_handler = view_handler
        self.order = order

    def __lt__(self, other):
        return self.order < other.order

    def handle_view(self, request):
        return self.view_handler(request)
