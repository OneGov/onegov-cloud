from onegov.core.utils import module_path
from onegov.org.theme import OrgTheme


# options editable by the user
user_options = {
    'primary-color': '#006fba',
    'footer-height': '38px'
}


class FeriennetTheme(OrgTheme):
    name = 'onegov.feriennet.foundation'

    # don't touch this number, it's incremented using bumpversion, so every
    # release will automatically trigger a rebuild of the theme
    version = '0.1.5'

    @property
    def post_imports(self):
        return super().post_imports + [
            'feriennet'
        ]

    @property
    def extra_search_paths(self):
        base_paths = super().extra_search_paths
        return [module_path('onegov.feriennet.theme', 'styles')] + base_paths
