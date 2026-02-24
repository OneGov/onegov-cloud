from __future__ import annotations

from onegov.core.utils import module_path
from onegov.org.theme import OrgTheme

NEWSGOT = '"NewsGot", Verdana, Arial, sans-serif;'

# options editable by the user
user_options = {
    'primary-color': '#e33521',
    'font-family-sans-serif': NEWSGOT
}


class WinterthurTheme(OrgTheme):
    name = 'onegov.winterthur.foundation'

    @property
    def post_imports(self) -> list[str]:
        return [*super().post_imports, 'winterthur']

    @property
    def extra_search_paths(self) -> list[str]:
        base_paths = super().extra_search_paths
        return [module_path('onegov.winterthur.theme', 'styles'), *base_paths]

    @property
    def pre_imports(self) -> list[str]:
        return [*super().pre_imports, 'winterthur-foundation-mods']
