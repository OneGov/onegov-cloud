import pytest
import os

from onegov.org.models.ticket import TicketDeletionMixin
from onegov.ticket import Handler
from onegov.ticket.errors import DuplicateHandlerError
from pathlib import Path
import importlib


def test_invalid_handler_code(handlers):

    # it's possible for the registry to not be empty due to other tests
    count = len(handlers.registry)

    with pytest.raises(AssertionError):
        handlers.register('abc', Handler)

    with pytest.raises(AssertionError):
        handlers.register('AB', Handler)

    assert len(handlers.registry) == count


def test_register_handler(handlers):

    class FooHandler(Handler):
        pass

    class BarHandler(Handler):
        pass

    handlers.register('FOO', FooHandler)
    handlers.register('BAR', BarHandler)

    assert handlers.get('FOO') == FooHandler
    assert handlers.get('BAR') == BarHandler

    with pytest.raises(DuplicateHandlerError):
        handlers.register('FOO', BarHandler)


def sources():
    """ the 'src' directory """
    return str(Path(__file__).parent.parent.parent.parent / 'src')


def discover_handler_implementations(directory):
    """
    In the a traverse through the source code this discovers every subclass
    implementation of the ‘Handler’ base class.
    """
    all_classes = {}

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                rel_path = os.path.relpath(root, directory)
                module_path = rel_path.replace(os.path.sep, '.')
                module_name = f"{module_path}.{file[:-3]}"\
                    if module_path != '.' else file[:-3]
                module_name = f"onegov.{module_name}"

                try:
                    mod = importlib.import_module(module_name)
                    new_classes = {
                        name: cls
                        for name, cls in mod.__dict__.items()
                        if (isinstance(cls, type) and issubclass(cls,
                                                                 Handler)
                            and cls != Handler)
                    }
                    all_classes.update(new_classes)
                except Exception as e:
                    print(f'failed to import {module_name}, {e}')

    return all_classes


def test_all_handlers_implement_deletion():
    """
        Generally, each handler should override the delete methods form
        TicketDeletionMixin, because this can't be defined in a generic way.

        When new handlers are introduced in the future, we expect them to
        support ticket deletion, unless specified otherwise.

        This test verifies that exceptions to this rule are at least *declared
        explicitly*.
    """

    src_path = Path(sources()) / "onegov"
    handler_class_dict = discover_handler_implementations(src_path)
    assert len(handler_class_dict) > 8

    def does_override_method_or_property(subclass, attr):
        return (attr in subclass.__dict__
                and attr in TicketDeletionMixin.__dict__)

    for handler_subclass in handler_class_dict.values():
        for delete_method in {'ticket_deletable', 'prepare_delete_ticket'}:
            assert does_override_method_or_property(
                handler_subclass, delete_method
            ), f"{handler_subclass} does not override {delete_method}"
