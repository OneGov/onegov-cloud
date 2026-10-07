from __future__ import annotations

import os

from onegov.foundation6 import BaseTheme
from onegov.bootstrap import BootstrapBaseTheme
from onegov.core.utils import module_path

from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence


HELVETICA = '"Helvetica Neue", Helvetica, Roboto, Arial, sans-serif !default'
ARIAL = 'Arial, sans-serif !default'
VERDANA = 'Verdana, Geneva, sans-serif !default'
COURIER_NEW = '"Courier New", Courier, monospace !default'     # monospace
ROBOTO_CONDENSED = '"Roboto Condensed", sans-serif !default'
MERRIWEATHER = 'Merriweather, sans-serif !default'

# "Merriweather","Helvetica Neue",Helvetica,Roboto,Arial,sans-serif
# options editable by the user
user_options = {
    'primary-color-ui': '#006fba',
    'body-font-family-ui': MERRIWEATHER,
    'header-font-family-ui': ROBOTO_CONDENSED
}

default_font_families = {
    'Roboto Condensed': ROBOTO_CONDENSED,
    'Helvetica': HELVETICA,
    'Arial': ARIAL,
    'Verdana': VERDANA,
    'Courier New': COURIER_NEW,
}


class TownBsTheme(BootstrapBaseTheme):
    name = 'onegov.town6.bootstrap'

    @property
    def default_options(self) -> dict[str, Any]:
        return {
            'primary': user_options['primary-color-ui'],
            'body-font-family': user_options['body-font-family-ui'],
            'headings-font-family': user_options['header-font-family-ui'],
        }

    @property
    def bootstrap_components(self) -> Sequence[str]:
        return (
            'reboot',
            'type',
            'images',
            'containers',
            'grid',
            'tables',
            'forms',
            'buttons',
            'transitions',
            'dropdown',
            'button-group',
            'nav',
            'navbar',
            'card',
            'accordion',
            'breadcrumb',
            'pagination',
            'badge',
            'alert',
            'progress',
            'list-group',
            'close',
            'toasts',
            'modal',
            'tooltip',
            'popover',
            'carousel',
            'spinners',
            'offcanvas',
            'placeholders',
            'helpers',
        )

    @property
    def pre_imports(self) -> list[str]:
        return [
            *self.additional_font_families,
            'bootstrap_customizations'
        ]

    @property
    def post_variable_imports(self) -> list[str]:
        return [
            'post_variable_imports'
        ]

    @property
    def post_imports(self) -> list[str]:
        """Our scss code split into various files"""
        return [
            'post_imports_customizations',
            'town',
            'custom_utilities',
            'custom_components',
            'homepage',
            'header',
            'navigation',
            'events_page',
            'forms_page',
            'search',
            'timeline',
        ]

    @property
    def extra_search_paths(self) -> list[str]:
        return [
            *super().extra_search_paths,
            module_path('onegov.town_bs.theme', 'styles'),
            self.font_search_path
        ]

    @property
    def font_search_path(self) -> str:
        """ Load fonts of the current theme folder and ignore fonts from
        parent applications if OrgTheme is inherited. """
        return module_path('onegov.town6.theme', 'fonts')

    @property
    def font_families(self) -> dict[str, str]:
        families = default_font_families.copy()
        families.update(self.additional_font_families)
        return families

    @property
    def additional_font_families(self) -> dict[str, str]:
        """ Filenames for use as labels in the settings and to construct the
        font-family string. Only sans-serif fonts are currently supported.
        """
        if not os.path.exists(self.font_search_path):
            return {}

        return {
            parts[0]: f'"{parts[0]}", {HELVETICA}'
            for filename in os.listdir(self.font_search_path)
            if (parts := filename.rpartition('.'))
            and parts[2] in ('css', 'scss')
        }
