from onegov.core.utils import module_path
from onegov.org.theme import OrgTheme


class SwissvotesTheme(OrgTheme):
    name = 'onegov.swissvotes.foundation'
    version = '0.0.1'

    @property
    def post_imports(self):
        return super().post_imports + ['swissvotes']

    @property
    def extra_search_paths(self):
        base_paths = super().extra_search_paths
        return [module_path('onegov.swissvotes.theme', 'styles')] + base_paths

    @property
    def pre_imports(self):
        return super().pre_imports + ['swissvotes-foundation-mods']
