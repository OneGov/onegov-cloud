from onegov.core.utils import module_path
from onegov.org.theme import OrgTheme


class AgencyTheme(OrgTheme):
    name = 'onegov.agency.foundation'

    @property
    def post_imports(self):
        return super().post_imports + [
            'agency',
            'chosen',
            'people',
            'ticket',
            'search'
        ]

    @property
    def extra_search_paths(self):
        base_paths = super().extra_search_paths
        return [module_path('onegov.agency.theme', 'styles')] + base_paths
