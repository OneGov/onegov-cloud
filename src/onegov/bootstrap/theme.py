from __future__ import annotations

import os.path

from collections import OrderedDict
from io import StringIO
from onegov.core.theme import Theme as CoreTheme
from onegov.core.theme import compile_sass

from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class BootstrapBaseTheme(CoreTheme):

    def __init__(self, compress: bool = True):
        """ Initializes the theme.

        :compress:
            If true, which is the default, the css is compressed before it is
            returned.

        """
        self.compress = compress

    @property
    def default_options(self) -> dict[str, Any]:
        """ Default options used when compiling the theme. """
        # return an ordered dict, in case someone overrides the compile options
        # with an ordered dict - this would otherwise result in an unordered
        # dict when both dicts are merged
        return OrderedDict()

    @property
    def variable_overrides(self) -> Mapping[str, str]:
        """ Bootstrap-Variablennamen -> Werte, werden VOR
        bootstrap/variables gesetzt (wegen !default). """
        return {}

    @property
    def bootstrap_components(self) -> Sequence[str]:
        """ Partial-Namen ohne Präfix, in Import-Reihenfolge. """
        return (
            'reboot',
            'type',
            'images',
            'containers',
            'grid',
            'tables',
            'forms',
            'buttons',
            'transitions',
            'dropdown',
            'button-group',
            'nav',
            'navbar',
            'card',
            'accordion',
            'breadcrumb',
            'pagination',
            'badge',
            'alert',
            'progress',
            'list-group',
            'close',
            'toasts',
            'modal',
            'tooltip',
            'popover',
            'carousel',
            'spinners',
            'offcanvas',
            'placeholders',
        )

    @property
    def pre_imports(self) -> list[str]:
        return []

    @property
    def post_variable_imports(self) -> list[str]:
        return []

    @property
    def post_imports(self) -> list[str]:
        return []

    @property
    def extra_search_paths(self) -> list[str]:
        return []

    @property
    def bootstrap_path(self) -> str:
        return os.path.join(
            os.path.dirname(__file__), 'scss')

    def compile(self, options: Mapping[str, Any] | None = None) -> str:
        _options = dict(self.default_options)
        option_values = dict(options or {})

        # We need to rename these options to match the variable names of
        # bootstrap
        if 'primary-color-ui' in option_values:
            option_values['primary'] = option_values['primary-color-ui']
        if 'body-font-family-ui' in option_values:
            option_values['body-font-family'] = (
                option_values['body-font-family-ui']
            )
        if 'header-font-family-ui' in option_values:
            option_values['headings-font-family'] = (
                option_values['header-font-family-ui']
            )

        _options.update(option_values)

        theme = StringIO()
        print('@charset "utf-8";', file=theme)

        print("@import 'functions';", file=theme)

        for key, value in _options.items():
            print(f'${key}: {value};', file=theme)

        print('\n'.join(f"@import '{i}';" for i in self.pre_imports),
              file=theme)

        print("@import 'variables';", file=theme)
        print("@import 'variables-dark';", file=theme)
        print("@import 'maps';", file=theme)

        print('\n'.join(f"@import '{i}';" for i in self.post_variable_imports),
                file=theme)

        print("@import 'mixins';", file=theme)
        print("@import 'root';", file=theme)

        for component in self.bootstrap_components:
            print(f"@import '{component}';", file=theme)

        print("@import 'utilities';", file=theme)
        print("@import 'utilities/api';", file=theme)

        print('\n'.join(f"@import '{i}';" for i in self.post_imports),
              file=theme)

        paths = self.extra_search_paths
        paths.append(self.bootstrap_path)

        return compile_sass(theme.getvalue(), paths, self.compress)
