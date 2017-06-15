from onegov.foundation import BaseTheme
from onegov.core.utils import module_path


class ElectionDayTheme(BaseTheme):
    name = 'onegov.election_day.foundation'

    # don't touch this number, it's incremented using bumpversion, so every
    # release will automatically trigger a rebuild of the theme
    version = '1.13.0'

    @property
    def post_imports(self):
        return [
            'election_day'
        ]

    @property
    def default_options(self):
        # Leave this empty, see below
        return {}

    def compile(self, options={}):
        # We cannot use the default_options attribute since we need to know
        # the primary color which happens to be in the options argument.
        # We merge the options and default options ourselve and call the
        # compile function of the base class
        _options = {
            'header-line-height': '1.3',
            'subheader-line-height': '1.3',
            'h1-font-reduction': 'rem-calc(15)',
            'h2-font-reduction': 'rem-calc(12)',
            'callout-panel-bg': 'scale-color({}, $lightness: 75%)'.format(
                options['primary-color']
            ),
            'topbar-bg-color': '#fff',
            'topbar-dropdown-bg': '#fff',
            'topbar-link-color': '#999',
            'topbar-link-color-hover': '#999',
            'topbar-link-color-active': options['primary-color'],
            'topbar-link-color-active-hover': options['primary-color'],
            'topbar-link-font-size': 'rem-calc(16)',
            'topbar-link-bg-hover': '#f9f9f9',
            'topbar-link-bg-active': '#fff',
            'topbar-link-bg-active-hover': '#f9f9f9',
            'topbar-link-padding': 'rem-calc(32)',
            'topbar-menu-link-color': '#999',
            'topbar-menu-icon-color': '#999',
        }
        _options.update(options)

        return super(ElectionDayTheme, self).compile(_options)

    @property
    def extra_search_paths(self):
        return [module_path('onegov.election_day.theme', 'styles')]
