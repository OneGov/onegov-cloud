from __future__ import annotations

from onegov.core.utils import module_path
from onegov.town6.theme import TownTheme


# options editable by the user
user_options = {
    'primary-color': '#1d487c',
}


class TranslatorDirectoryTheme(TownTheme):
    name = 'onegov.translator_directory.theme'

    @property
    def post_imports(self) -> list[str]:
        return [*super().post_imports, 'translator_directory']

    @property
    def extra_search_paths(self) -> list[str]:
        base_paths = super().extra_search_paths
        return [
            module_path('onegov.translator_directory.theme', 'styles'),
            *base_paths
        ]
