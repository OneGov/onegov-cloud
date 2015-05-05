from onegov.foundation import BaseTheme
from onegov.core.utils import module_path


# the colors which are editable by the user
user_colors = {
    'primary-color': '#006fba'
}


class TownTheme(BaseTheme):
    name = 'onegov.town.foundation'

    # don't touch this number, it's incremented using bumpversion, so every
    # release will automatically trigger a rebuild of the theme
    version = '0.0.2'

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
            'topbar-menu-link-color': '#312f2e',
            'topbar-menu-icon-color': '#312f2e',
            'topbar-dropdown-bg': '#f5f5f5',
            'side-nav-font-weight-active': 'bold',
            'crumb-bg': '#fff',
            'crumb-border-size': '0',
            'tile-image-1': '"../static/homepage-images/tile-1-small.jpg"',
            'tile-image-2': '"../static/homepage-images/tile-2-small.jpg"',
            'tile-image-3': '"../static/homepage-images/tile-3-small.jpg"',
            'tile-image-4': '"../static/homepage-images/tile-4-small.jpg"',
            'tile-image-5': '"../static/homepage-images/tile-5-small.jpg"',
            'tile-image-6': 'null'
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
