from onegov.foundation import BaseTheme
from onegov.core.utils import module_path


# the colors which are editable by the user
user_colors = {
    'primary-color': '#006fba'
}


class TownTheme(BaseTheme):
    name = 'onegov.town.foundation'
    version = '1.0'

    @property
    def default_options(self):
        options = {
            'top-bar-border-size': '0.3rem',
            'bottom-links-color': '#777',
            'bottom-links-size': '0.8rem',
            'topbar-bg-color': '#f5f5f5',
            'topbar-link-bg-hover': '#dfdfdf',
            'topbar-link-color': '#312f2e',
            'topbar-link-color-hover': '#312f2e',
            'topbar-link-color-active': '#312f2e',
            'topbar-link-color-active-hover': '#312f2e',
            'topbar-link-weight': 'bold',
        }
        options.update(user_colors)

        return options

    @property
    def post_imports(self):
        return [
            'town'
        ]

    @property
    def extra_search_paths(self):
        return [module_path('onegov.town.theme', 'styles')]
