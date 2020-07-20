import os.path
import textwrap

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

    use_prototype = False
    use_flex = False

    @property
    def foundation_helpers(self):
        return textwrap.dedent("""
        @include foundation-float-classes;
        @if $flex { @include foundation-flex-classes; }
        @include foundation-visibility-classes;
        @if $prototype { @include foundation-prototype-classes; }
        """)

    @property
    def foundation_config_vars(self):
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
    def foundation_grid(self):
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
    def foundation_styles(self):
        """The default styles"""
        return 'global-styles', 'forms', 'typography'

    @property
    def foundation_components(self):
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

    @property
    def get_foundation_file(self):
        """
        Create the foundation.scss in code, since the pre_imports
        must go there. Afterwards, in def compile, all the includes are added.
        We import everything by default, and the include what is needed by
        foundation_components.
        """
        deps = 'missing-dependencies'
        pre_imports = '\n'.join(f"@import '{i}';" for i in self.pre_imports)
        post_imports = '\n'.join(f"@import '{i}';" for i in self.post_imports)
        fp = 'foundation/scss'
        _vendor = 'foundation/_vendor'
        return textwrap.dedent(f"""
        /**
         * Foundation for Sites
         * Version 6.6.3
         * https://get.foundation
         * Licensed under MIT Open Source
         */
        
        // --- Dependencies ---
        @import '{fp}/vendor/normalize';
        @import '{_vendor}/sassy-lists/stylesheets/helpers/{deps}';
        @import '{_vendor}/sassy-lists/stylesheets/helpers/true';
        @import '{_vendor}/sassy-lists/stylesheets/functions/contain';
        @import '{_vendor}/sassy-lists/stylesheets/functions/purge';
        @import '{_vendor}/sassy-lists/stylesheets/functions/remove';
        @import '{_vendor}/sassy-lists/stylesheets/functions/replace';
        @import '{_vendor}/sassy-lists/stylesheets/functions/to-list';

        @import '{fp}/_settings';

        {pre_imports}
        
        // --- Components ---
        // Utilities
        @import '{fp}/util/util';
        // Global styles
        @import '{fp}/global';
        @import '{fp}/forms/forms';
        @import '{fp}/typography/typography';
        
        // Grids
        @import '{fp}/grid/grid';
        @import '{fp}/xy-grid/xy-grid';
        // Generic components
        @import '{fp}/components/button';
        @import '{fp}/components/button-group';
        @import '{fp}/components/close-button';
        @import '{fp}/components/label';
        @import '{fp}/components/progress-bar';
        @import '{fp}/components/slider';
        @import '{fp}/components/switch';
        @import '{fp}/components/table';
        // Basic components
        @import '{fp}/components/badge';
        @import '{fp}/components/breadcrumbs';
        @import '{fp}/components/callout';
        @import '{fp}/components/card';
        @import '{fp}/components/dropdown';
        @import '{fp}/components/pagination';
        @import '{fp}/components/tooltip';
        
        // Containers
        @import '{fp}/components/accordion';
        @import '{fp}/components/media-object';
        @import '{fp}/components/orbit';
        @import '{fp}/components/responsive-embed';
        @import '{fp}/components/tabs';
        @import '{fp}/components/thumbnail';
        // Menu-based containers
        @import '{fp}/components/menu';
        @import '{fp}/components/menu-icon';
        @import '{fp}/components/accordion-menu';
        @import '{fp}/components/drilldown';
        @import '{fp}/components/dropdown-menu';
        
        // Layout components
        @import '{fp}/components/off-canvas';
        @import '{fp}/components/reveal';
        @import '{fp}/components/sticky';
        @import '{fp}/components/title-bar';
        @import '{fp}/components/top-bar';
        
        // Helpers
        @import '{fp}/components/float';
        @import '{fp}/components/flex';
        @import '{fp}/components/visibility';
        @import '{fp}/prototype/prototype';

        {post_imports}
        """)

    @property
    def includes(self):
        not_allowed = ('flex-classes', 'flex-grid', 'grid', 'xy-grid-classes',
                       'visibility-classes', 'prototype-classes',
                       'float-classes', 'global-styles', 'forms', 'typography')
        for cmp in self.foundation_components:
            assert cmp not in not_allowed, f'{cmp} not supposed to go in here'

        return chain(
            (var_ for var_ in self.foundation_config_vars),
            (f'@include foundation-{i};' for i in self.foundation_styles),
            (self.foundation_grid, ),
            (f"@include foundation-{i};" for i in self.foundation_components),
            (self.foundation_helpers, )
        )

    def compile(self, options={}):
        """ Compiles the theme with the given options. """

        # copy, because the dict may be static if it's a basic property
        _options = self.default_options.copy()
        _options.update(options)

        theme = StringIO()

        print('@charset "utf-8";', file=theme)

        for key, value in _options.items():
            print(f"${key}: {value};", file=theme)

        print(self.get_foundation_file, file=theme)

        print("\n".join(self.includes), file=theme)

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

        class App(FoundationApp):
            theme_options = {
                'rowWidth': '1200px'
            }

        @App.setting(section='core', name='theme')
        def get_theme():
            return Theme()

    """
    name = 'zurb.foundation'
