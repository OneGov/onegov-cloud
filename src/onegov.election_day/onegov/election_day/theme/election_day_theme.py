from onegov.foundation import BaseTheme
from onegov.core.utils import module_path


class ElectionDayTheme(BaseTheme):
    name = 'onegov.election_day.foundation'

    # don't touch this number, it's incremented using bumpversion, so every
    # release will automatically trigger a rebuild of the theme
    version = '1.4.0'

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
            )
        }
        _options.update(options)

        return super(ElectionDayTheme, self).compile(_options)

    @property
    def extra_search_paths(self):
        return [module_path('onegov.election_day.theme', 'styles')]
