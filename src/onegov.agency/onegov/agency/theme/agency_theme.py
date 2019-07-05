from onegov.core.utils import module_path
from onegov.org.theme import OrgTheme


class AgencyTheme(OrgTheme):
    name = 'onegov.agency.foundation'

    # don't touch this number, it's incremented using bumpversion, so every
    # release will automatically trigger a rebuild of the theme
    version = '1.12.0'

    @property
    def post_imports(self):
        return super().post_imports + [
            'agency',
            'chosen',
            'people',
            'ticket'
        ]

    @property
    def extra_search_paths(self):
        base_paths = super().extra_search_paths
        return [module_path('onegov.agency.theme', 'styles')] + base_paths
