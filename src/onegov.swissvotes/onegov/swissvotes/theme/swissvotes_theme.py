from onegov.core.utils import module_path
from onegov.foundation import BaseTheme


class SwissvotesTheme(BaseTheme):
    name = 'onegov.swissvotes.foundation'
    version = '0.0.6'

    @property
    def pre_imports(self):
        return ['swissvotes-foundation-mods']

    @property
    def post_imports(self):
        return super().post_imports + [
            'mixin',
            'header',
            'footer',
            'form',
            'table',
            'alert',
            'swissvotes'
        ]

    @property
    def extra_search_paths(self):
        base_paths = super().extra_search_paths
        return [module_path('onegov.swissvotes.theme', 'styles')] + base_paths
