from onegov.core.utils import module_path
from onegov.org.theme import OrgTheme


from onegov.org.theme.org_theme import HELVETICA

# options editable by the user
user_options = {
    'primary-color-ui': '#006fba',
    'body-font-family-ui': HELVETICA,
    'header-font-family-ui': HELVETICA,

}


class TownTheme(OrgTheme):
    name = 'onegov.town.foundation'

    @property
    def post_imports(self):
        return super().post_imports + [
            'town'
        ]

    @property
    def extra_search_paths(self):
        base_paths = super().extra_search_paths
        return [module_path('onegov.town.theme', 'styles')] + base_paths

    @property
    def font_search_path(self):
        return module_path('onegov.org.theme', 'fonts')
