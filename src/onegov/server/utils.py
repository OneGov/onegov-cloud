import inspect
import importlib


def load_class(cls):
    """ Loads the given class from string (unless alrady a class). """

    if inspect.isclass(cls):
        return cls

    module_name, class_name = cls.rsplit('.', 1)
    module = importlib.import_module(module_name)

    return getattr(module, class_name, None)
