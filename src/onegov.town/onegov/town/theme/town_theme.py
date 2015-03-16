from onegov.foundation import BaseTheme
from onegov.core.utils import module_path


class TownTheme(BaseTheme):
    name = 'onegov.town.foundation'
    version = '1.0'

    @property
    def default_options(self):
        return {
            # this part should be configurable by the user in the future:
            # >>>
            'primary-color': '#006fba',
            # <<<
            'topbar-bg-color': '#f5f5f5',
            'topbar-link-bg-hover': '#dfdfdf',
            'topbar-link-color': '#312f2e',
            'topbar-link-color-hover': '#312f2e',
            'topbar-link-color-active': '#312f2e',
            'topbar-link-color-active-hover': '#312f2e',
            'topbar-link-weight': 'bold',
        }

    @property
    def post_imports(self):
        return [
            'town'
        ]

    @property
    def extra_search_paths(self):
        return [module_path('onegov.town.theme', 'styles')]
