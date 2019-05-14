from onegov.core.utils import module_path
from onegov.foundation import BaseTheme


class WtfsTheme(BaseTheme):
    name = 'onegov.wtfs.foundation'
    version = '1.2.6'

    @property
    def pre_imports(self):
        return ['wtfs-foundation-mods']

    @property
    def post_imports(self):
        return super().post_imports + [
            'mixin',
            'header',
            'footer',
            'form',
            'chosen',
            'table',
            'alert',
            'wtfs'
        ]

    @property
    def extra_search_paths(self):
        base_paths = super().extra_search_paths
        return [module_path('onegov.wtfs.theme', 'styles')] + base_paths
