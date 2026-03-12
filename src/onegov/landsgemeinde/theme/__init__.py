from __future__ import annotations

from onegov.core.utils import module_path
from onegov.town6.theme import TownTheme


class LandsgemeindeTheme(TownTheme):
    name = 'onegov.landsgemeinde.theme'

    @property
    def post_imports(self) -> list[str]:
        return [
            *super().post_imports,
            'landsgemeinde',
            'ticker',
            'landsgemeinde_print',
        ]

    @property
    def extra_search_paths(self) -> list[str]:
        base_paths = super().extra_search_paths
        return [
            module_path('onegov.landsgemeinde.theme', 'styles'),
            *base_paths
        ]
