import os.path
import sass

from collections import OrderedDict
from itertools import chain
from io import StringIO
from onegov.core.theme import Theme as CoreTheme


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
    before it is compiled::

        @import 'foundation/functions';

        $rowWidth: 1000px;
        $columnGutter: 30px;

    If your variables rely on a certain order you need to pass an ordered dict.

    """

    def __init__(self, compress=True):
        """ Initializes the theme.

        :compress:
            If true, which is the default, the css is compressed before it is
            returned.

        """
        self.compress = compress

    @property
    def default_options(self):
        """ Default options used when compiling the theme. """
        # return an ordered dict, in case someone overrides the compile options
        # with an ordered dict - this would otherwise result in an unordered
        # dict when both dicts are merged
        return OrderedDict()

    @property
    def pre_imports(self):
        """ Imports added before the foundation import. The imports must be
        found in one of the paths (see :attr:`extra_search_paths`).

        The form of a single import is 'example' (which would search for
        files named 'example.scss')

        """
        return []

    @property
    def foundation_components(self):
        """ Foundation components without the prefix as in app.scss that will
        be included. """
        return (
            'global-styles',
            'forms',
            'typography',
            'xy-grid-classes',
            'grid',
            # 'flex-grid',
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
            'float-classes',
            'flex-classes',
            'visibility-classes',
            'prototype-classes'
        )

    @property
    def imports(self):
        """ All imports, including the foundation ones. Override with care. """
        return chain(
            (f"@import '{i}';" for i in self.pre_imports),
            (f"@include foundation-{i};" for i in self.foundation_components),
            (f"@import '{i}';" for i in self.post_imports),
            # ('fixes', ),
        )

    @property
    def post_imports(self):
        """
        Imports added after the foundation import. The imports must be found
        in one of the paths (see :attr:`extra_search_paths`).

        The form of a single import is 'example' (which would search for
        files named 'example.scss')

        """
        return []

    @property
    def extra_search_paths(self):
        """ A list of absolute search paths added before the actual foundation
        search path.

        """
        return []

    @property
    def foundation_path(self):
        """ The search path for the foundation files included in this module.

        """
        return os.path.join(os.path.dirname(__file__), 'foundation')

    def compile(self, options={}):
        """ Compiles the theme with the given options. """

        # copy, because the dict may be static if it's a basic property
        _options = self.default_options.copy()
        _options.update(options)

        theme = StringIO()

        # As the mixins are not exported, we include them like in app.scss
        print('@charset "utf-8";', file=theme)
        print("@import 'foundation/settings/settings';", file=theme)
        print("@import 'foundation/foundation';", file=theme)

        for key, value in _options.items():
            print(f"${key}: {value};", file=theme)

        print("\n".join(self.imports), file=theme)

        paths = self.extra_search_paths
        paths.append(self.foundation_path)

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

        class App(Framework):
            theme_options = {
                'rowWidth': '1200px'
            }

        @App.setting(section='core', name='theme')
        def get_theme():
            return Theme()

    """
    name = 'zurb.foundation'
