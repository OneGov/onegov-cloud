from __future__ import annotations

import os

from onegov.foundation import BaseTheme
from onegov.core.utils import module_path


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence


HELVETICA = '"Helvetica Neue", Helvetica, Roboto, Arial, sans-serif !default;'
ARIAL = 'Arial, sans-serif !default;'
VERDANA = 'Verdana, Geneva, sans-serif !default;'
COURIER_NEW = '"Courier New", Courier, monospace !default;'     # monospace

# options editable by the user
user_options = {
    'primary-color': '#006fba',
    'font-family-sans-serif': HELVETICA
}

default_font_families = {
    'Helvetica': HELVETICA,
    'Arial': ARIAL,
    'Verdana': VERDANA,
    'Courier New': COURIER_NEW,
}


class OrgTheme(BaseTheme):
    name = 'onegov.org.foundation'

    _force_compile = False

    @property
    def default_options(self) -> dict[str, Any]:
        return user_options

    @property
    def foundation_components(self) -> Sequence[str]:
        return (
            'grid',
            'accordion',
            'alert-boxes',
            'block-grid',
            'breadcrumbs',
            'button-groups',
            'buttons',
            'dropdown',
            'dropdown-buttons',
            'forms',
            'inline-lists',
            'labels',
            'orbit',
            'pagination',
            'panels',
            'progress-bars',
            'reveal',
            'side-nav',
            'switches',
            'split-buttons',
            'sub-nav',
            'tables',
            'thumbs',
            'tooltips',
            'top-bar',
            'type',
            'visibility'
        )

    @property
    def pre_imports(self) -> list[str]:
        return [
            'foundation-mods',
            *self.additional_font_families
        ]

    @property
    def post_imports(self) -> list[str]:
        return [
            'org',
            'chosen',
            'bar-graph'
        ]

    @property
    def extra_search_paths(self) -> list[str]:
        return [
            module_path('onegov.org.theme', 'styles'),
            self.font_search_path
        ]

    @property
    def font_search_path(self) -> str:
        """ Load fonts of the current theme folder and ignore fonts from
        parent applications if OrgTheme is inherited. """
        module = self.name.replace('foundation', 'theme')
        return module_path(module, 'fonts')

    @property
    def font_families(self) -> dict[str, str]:
        families = default_font_families.copy()
        families.update(self.additional_font_families)
        return families

    @property
    def additional_font_families(self) -> dict[str, str]:
        """ Returns the filenames as they are to use as label in the settings
        as well as to construct the font-family string.
        Only sans-serif fonts are supported by now.
        """
        if not os.path.exists(self.font_search_path):
            return {}

        def fn(n: str) -> list[str]:
            return n.split('.')

        return {
            fn(n)[0]: f'"{fn(n)[0]}", {HELVETICA}' for n in os.listdir(
                self.font_search_path) if fn(n)[1] in ('css', 'scss')
        }
