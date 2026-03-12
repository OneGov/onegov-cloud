from __future__ import annotations

from onegov.foundation import BaseTheme
from onegov.core.utils import module_path


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping


class ElectionDayTheme(BaseTheme):
    name = 'onegov.election_day.foundation'

    @property
    def post_imports(self) -> list[str]:
        return [
            'election_day'
        ]

    @property
    def default_options(self) -> dict[str, Any]:
        # Leave this empty, see below
        return {}

    def compile(self, options: Mapping[str, Any] | None = None) -> str:
        # We cannot use the default_options attribute since we need to know
        # the primary color which happens to be in the options argument.
        # We merge the options and default options ourselve and call the
        # compile function of the base class
        assert options is not None
        _options = {
            'header-line-height': '1.3',
            'subheader-line-height': '1.3',
            'h1-font-reduction': 'rem-calc(15)',
            'h2-font-reduction': 'rem-calc(12)',
            'callout-panel-bg': '#ecfaff',
            'topbar-bg-color': '#fff',
            'topbar-dropdown-bg': '#fff',
            'topbar-link-color': '#999',
            'topbar-link-color-hover': '#999',
            'topbar-link-color-active': options['primary-color'],
            'topbar-link-color-active-hover': options['primary-color'],
            'topbar-link-font-size': 'rem-calc(16)',
            'topbar-link-bg-hover': '#f9f9f9',
            'topbar-link-bg-active': '#fff',
            'topbar-link-bg-active-hover': '#f9f9f9',
            'topbar-link-padding': 'rem-calc(32)',
            'topbar-menu-link-color': '#999',
            'topbar-menu-icon-color': '#999',
        }
        _options.update(options or {})

        return super().compile(_options)

    @property
    def extra_search_paths(self) -> list[str]:
        return [module_path('onegov.election_day.theme', 'styles')]
