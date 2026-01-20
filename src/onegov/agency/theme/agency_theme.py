from __future__ import annotations

from onegov.core.utils import module_path
from onegov.org.theme import OrgTheme


class AgencyTheme(OrgTheme):
    name = 'onegov.agency.foundation'

    @property
    def post_imports(self) -> list[str]:
        return [
            *super().post_imports,
            'agency',
            'chosen',
            'people',
            'ticket',
            'search'
        ]

    @property
    def extra_search_paths(self) -> list[str]:
        base_paths = super().extra_search_paths
        return [module_path('onegov.agency.theme', 'styles'), *base_paths]
