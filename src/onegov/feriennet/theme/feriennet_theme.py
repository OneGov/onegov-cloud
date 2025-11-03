from __future__ import annotations

from onegov.core.utils import module_path
from onegov.town6.theme import TownTheme


# options editable by the user
user_options = {
    'primary-color': '#006fba',
}


class FeriennetTheme(TownTheme):
    name = 'onegov.feriennet.foundation'

    @property
    def post_imports(self) -> list[str]:
        return [*super().post_imports, 'feriennet']

    @property
    def extra_search_paths(self) -> list[str]:
        base_paths = super().extra_search_paths
        return [module_path('onegov.feriennet.theme', 'styles'), *base_paths]
