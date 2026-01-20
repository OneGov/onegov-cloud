from __future__ import annotations

from functools import lru_cache
from findimports import ModuleGraph  # type: ignore[import-untyped]
from pathlib import Path

from onegov.core import LEVELS


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from os import PathLike


def test_hierarchy() -> None:
    """ Originally, onegov.* modules were separated into separate repositories
    and deployed individually to PyPI.

    This meant that each module would list the dependencies it needed,
    including other onegov.* modules. As a side-effect, this ensured that
    a module like onegov.core would not import from onegov.org, creating
    an undesired dependency.

    With the move to a single repository and a container build, we lost this
    side-effect. It is now possible for onegov.core to import from onegov.org
    and that is not something we want, because things like the core should
    not import from modules higher up the chain.

    This test ensures that this restriction is still honored.

    Each module is put into a level. Modules may import from the same level
    or the levels below, but not from the levels above.

    The current list of levels is also used for the upgrade step order. It can
    be found in `onegov.core.__init__.py`.

    This is not exactly equivalent to what we had before, but it is good
    basic check to ensure that we do not add unwanted dependencies.

    """

    modules = level_by_module(LEVELS)

    # all modules must be defined
    for module in existing_modules():
        assert module in modules, f"module not defined in hierarchy: {module}"

    # graph all imports
    graph = ModuleGraph()
    graph.parsePathname(str(sources()))

    # ensure hierarchy
    for id, module in graph.modules.items():
        name = module_name(module.filename)

        if name is None:
            continue

        allowed = allowed_imports(LEVELS, name)

        for imported in module.imported_names:
            import_name = '.'.join(imported.name.split('.')[:2])

            if not import_name.startswith('onegov'):
                continue

            assert import_name in allowed, \
                f"Invalid import {name} → {import_name} in {imported.filename}"


def allowed_imports(levels: Sequence[Sequence[str]], module: str) -> set[str]:
    """ Given a module name, returns an imprtable set of onegov modules. """

    allowed: set[str] = set()

    for modules in levels:
        allowed.update(modules)

        if module in modules:
            return allowed

    raise AssertionError(f"unknown module: {module}")


def sources() -> Path:
    """ Returns the path to 'src'. """
    return Path(__file__).parent.parent / 'src'


@lru_cache(maxsize=128)
def module_name(path: PathLike[str]) -> str | None:
    """ Given a path, returns the onegov module, or None, if not a onegov
    module (and therefore not relevant to this analysis).

    """
    namespace = sources() / 'onegov'

    if namespace in Path(path).parents:

        name = str(path).replace(str(namespace), '')\
            .strip('/')\
            .split('/', 1)[0]

        return f'onegov.{name}'
    return None


def level_by_module(levels: Sequence[Sequence[str]]) -> dict[str, int]:
    """ Returns a dictionary with modules -> level. """

    result = {}

    for level, modules in enumerate(levels):
        for module in modules:
            assert module not in result, f"duplicate module: {module}"

            result[module] = level

    return result


def existing_modules() -> Iterator[str]:
    """ Yields the module names found in the src/onegov folder. """

    for child in (sources() / 'onegov').iterdir():
        if child.is_dir():
            yield f'onegov.{child.name}'
