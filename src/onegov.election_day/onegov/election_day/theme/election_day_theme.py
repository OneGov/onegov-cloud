from onegov.foundation import BaseTheme
from onegov.core.utils import module_path


class ElectionDayTheme(BaseTheme):
    name = 'onegov.election_day.foundation'

    # don't touch this number, it's incremented using bumpversion, so every
    # release will automatically trigger a rebuild of the theme
    version = '1.0.4'

    @property
    def post_imports(self):
        return [
            'election_day'
        ]

    @property
    def default_options(self):
        return {
            'header-line-height': '1.3',
            'subheader-line-height': '1.3',
            'h1-font-reduction': 'rem-calc(15)',
            'h2-font-reduction': 'rem-calc(12)',
        }

    @property
    def extra_search_paths(self):
        return [module_path('onegov.election_day.theme', 'styles')]
