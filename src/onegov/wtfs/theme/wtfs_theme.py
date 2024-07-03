from onegov.core.utils import module_path
from onegov.foundation import BaseTheme


class WtfsTheme(BaseTheme):
    name = 'onegov.wtfs.foundation'

    @property
    def pre_imports(self) -> list[str]:
        return ['font-newsgot', 'wtfs-foundation-mods']

    @property
    def post_imports(self) -> list[str]:
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
    def extra_search_paths(self) -> list[str]:
        base_paths = super().extra_search_paths
        return [module_path('onegov.wtfs.theme', 'styles')] + base_paths
