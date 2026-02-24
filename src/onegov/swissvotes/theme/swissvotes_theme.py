from __future__ import annotations

from onegov.core.utils import module_path
from onegov.foundation import BaseTheme


class SwissvotesTheme(BaseTheme):
    name = 'onegov.swissvotes.foundation'

    @property
    def pre_imports(self) -> list[str]:
        return ['swissvotes-foundation-mods']

    @property
    def post_imports(self) -> list[str]:
        return [
            *super().post_imports,
            'mixin',
            'header',
            'mastodon',
            'footer',
            'form',
            'table',
            'alert',
            'dropzone',
            'swissvotes'
        ]

    @property
    def extra_search_paths(self) -> list[str]:
        base_paths = super().extra_search_paths
        return [module_path('onegov.swissvotes.theme', 'styles'), *base_paths]
