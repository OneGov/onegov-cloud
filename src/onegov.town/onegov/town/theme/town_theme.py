from onegov.core.utils import module_path
from onegov.org.theme import OrgTheme


# options editable by the user
user_options = {
    'primary-color': '#006fba',
    'footer-height': '38px'
}


class TownTheme(OrgTheme):
    name = 'onegov.town.foundation'

    # don't touch this number, it's incremented using bumpversion, so every
    # release will automatically trigger a rebuild of the theme
    version = '1.13.1'

    @property
    def post_imports(self):
        return super().post_imports + [
            'town'
        ]

    @property
    def extra_search_paths(self):
        base_paths = super().extra_search_paths
        return [module_path('onegov.town.theme', 'styles')] + base_paths
