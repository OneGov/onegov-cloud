from __future__ import annotations

import os.path
import textwrap

import sass

from collections import OrderedDict
from itertools import chain
from io import StringIO
from onegov.core.theme import Theme as CoreTheme


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence


class BaseTheme(CoreTheme):
    """ Base class for Zurb Foundation based themes. Use this class to
    create a theme that customizes Zurb Foundation somehow.

    If you don't want to customize it at all, use :class:`Theme`.

    To customize start like this::

        from onegov.foundation import BaseTheme

        class MyTheme(BaseTheme):
            name = 'my-theme'
            version = '1.0'

    You can then add paths with your own scss files, as well as imports that
    should be added *before* the foundation theme, and imports that should
    be added *after* the foundation theme.

    Finally, options passed to the :meth:`compile` function take this form::

        options = {
            'rowWidth': '1000px',
            'columnGutter': '30px'
        }

    Those options result in variables added at the very top of the sass source
    (but after the _settings.scss) before it is compiled::

        $rowWidth: 1000px;
        $columnGutter: 30px;

    If your variables rely on a certain order you need to pass an ordered dict.

    If use_flex is set to False on the theme itself,
    the float grid is used instead.

    If $xy-grid is set to false by the subclassing theme,
    the flex grid is used.

    """

    _uninitialized_vars = (
        'primary-color',
        'secondary-color',
        'success-color',
        'warning-color',
        'alert-color',
        '-zf-size',
        '-zf-bp-value'
    )

    include_motion_ui = False

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
    def pre_imports(self) -> list[str]:
        """ Imports added before the foundation import. The imports must be
        found in one of the paths (see :attr:`extra_search_paths`).

        The form of a single import is 'example' (which would search for
        files named 'example.scss')

        """
        return []

    use_prototype = False
    use_flex = False

    @property
    def foundation_helpers(self) -> str:
        return textwrap.dedent("""
        @include foundation-float-classes;
        @if $flex { @include foundation-flex-classes; }
        @include foundation-visibility-classes;
        @if $prototype { @include foundation-prototype-classes; }
        """)

    @property
    def foundation_config_vars(self) -> Sequence[str]:
        vars = []
        vars.append(
            f'$flex: {"true" if self.use_flex else "false"};\n'
            f'$prototype: {"true" if self.use_prototype else "false"};\n'
            '$xy-grid: $xy-grid;'
        )

        vars.append(textwrap.dedent("""
            @if $flex {
              $global-flexbox: true !global;
            }
            @if $xy-grid {
              $xy-grid: true !global;
            }"""))
        return vars

    @property
    def foundation_grid(self) -> str:
        """Defines the settings that are grid related as in the mixin
        foundation_everything. """
        return textwrap.dedent("""
        @if not $flex {
          @include foundation-grid;
        }
        @else {
          @if $xy-grid {
            @include foundation-xy-grid-classes;
          }
          @else {
            @include foundation-flex-grid;
          }
        }
        """)

    @property
    def foundation_styles(self) -> Sequence[str]:
        """The default styles"""
        return 'global-styles', 'forms', 'typography'

    @property
    def foundation_components(self) -> tuple[str, ...]:
        """ Foundation components except the grid without the prefix as in
        app.scss that will be included. Be aware that order matters. These are
        included, not imported."""
        return (
            'button',
            'button-group',
            'close-button',
            'label',
            'progress-bar',
            'slider',
            'switch',
            'table',
            'badge',
            'breadcrumbs',
            'callout',
            'card',
            'dropdown',
            'pagination',
            'tooltip',
            'accordion',
            'media-object',
            'orbit',
            'responsive-embed',
            'tabs',
            'thumbnail',
            'menu',
            'menu-icon',
            'accordion-menu',
            'drilldown-menu',
            'dropdown-menu',
            'off-canvas',
            'reveal',
            'sticky',
            'title-bar',
            'top-bar',
        )

    @property
    def foundation_motion_ui(self) -> Sequence[str]:
        if self.include_motion_ui:
            return 'motion-ui-transitions', 'motion-ui-animations'
        return []

    @property
    def post_imports(self) -> list[str]:
        """
        Imports added after the foundation import. The imports must be found
        in one of the paths (see :attr:`extra_search_paths`).

        The form of a single import is 'example' (which would search for
        files named 'example.scss')

        """
        return []

    @property
    def extra_search_paths(self) -> list[str]:
        """ A list of absolute search paths added before the actual foundation
        search path.

        """
        return []

    @property
    def foundation_path(self) -> str:
        """ The search path for the foundation files included in this module.

        """
        return os.path.join(
            os.path.dirname(__file__), 'foundation', 'foundation', 'scss')

    @property
    def vendor_path(self) -> str:
        """ The search path for the foundation files included in this module.

        """
        return os.path.join(
            os.path.dirname(__file__), 'foundation', 'vendor')

    @property
    def includes(self) -> Iterator[str]:
        not_allowed = ('flex-classes', 'flex-grid', 'grid', 'xy-grid-classes',
                       'visibility-classes', 'prototype-classes',
                       'float-classes', 'global-styles', 'forms', 'typography')
        for cmp in self.foundation_components:
            assert cmp not in not_allowed, f'{cmp} not supposed to go in here'

        return chain(
            (var_ for var_ in self.foundation_config_vars),
            (f'@include foundation-{i};' for i in self.foundation_styles),
            (self.foundation_grid, ),
            (f'@include foundation-{i};' for i in self.foundation_components),
            (self.foundation_helpers, ),
            (f'@include {i};' for i in self.foundation_motion_ui)
        )

    def compile(self, options: Mapping[str, Any] | None = None) -> str:
        """ Compiles the theme with the given options. """

        # copy, because the dict may be static if it's a basic property
        _options = self.default_options.copy()
        _options.update(options or {})

        theme = StringIO()

        print('@charset "utf-8";', file=theme)

        # Fix depreciation warnings
        print('\n'.join(
            f'${var}: null;' for var in self._uninitialized_vars), file=theme)

        for key, value in _options.items():
            print(f'${key}: {value};', file=theme)

        print('\n'.join(
            f"@import '{i}';" for i in self.pre_imports), file=theme)

        print('@include add-foundation-colors;', file=theme)
        print("@import 'foundation';", file=theme)

        if self.include_motion_ui:
            print("@import 'motion-ui/motion-ui';", file=theme)

        print('\n'.join(
            f"@import '{i}';" for i in self.post_imports), file=theme)

        print('\n'.join(self.includes), file=theme)

        paths = self.extra_search_paths
        paths.append(self.foundation_path)
        if self.include_motion_ui:
            paths.append(self.vendor_path)
        return sass.compile(
            string=theme.getvalue(),
            include_paths=paths,
            output_style='compressed' if self.compress else 'nested'
        )


class Theme(BaseTheme):
    """ Zurb Foundation vanilla theme. Use this if you don't want any changes
    to zurb foundation, except for setting supported variables.

    Do not use this class as a base for your own theme!

    Example::

        from onegov.core import Framework
        from onegov.foundation import Theme

        class App(FoundationApp):
            theme_options = {
                'rowWidth': '1200px'
            }

        @App.setting(section='core', name='theme')
        def get_theme():
            return Theme()

    """
    name = 'zurb.foundation'
