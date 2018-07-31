from onegov.core.utils import module_path
from onegov.org.theme import OrgTheme


# options editable by the user
user_options = {
    'primary-color': '#e33521',
    'footer-height': '38px'
}


class WinterthurTheme(OrgTheme):
    name = 'onegov.winterthur.foundation'

    # don't touch this number, it's incremented using bumpversion, so every
    # release will automatically trigger a rebuild of the theme
    version = '0.2.12'

    @property
    def post_imports(self):
        return super().post_imports + [
            'winterthur'
        ]

    @property
    def extra_search_paths(self):
        base_paths = super().extra_search_paths
        return [module_path('onegov.winterthur.theme', 'styles')] + base_paths

    @property
    def pre_imports(self):
        return super().pre_imports + [
            'font-newsgot',
            'winterthur-foundation-mods'
        ]
