from onegov.core.utils import module_path
from onegov.town6.theme import TownTheme


class PasTheme(TownTheme):
    name = 'onegov.pas.theme'

    @property
    def post_imports(self) -> list[str]:
        return super().post_imports + [
            'pas',
        ]

    @property
    def extra_search_paths(self) -> list[str]:
        base_paths = super().extra_search_paths
        return [
            module_path('onegov.pas.theme', 'styles')
        ] + base_paths
