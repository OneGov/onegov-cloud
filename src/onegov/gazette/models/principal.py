from __future__ import annotations

from yaml import safe_load


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Self


class Principal:
    """ The principal is the political entity running the gazette app. """

    CANTONS = {
        'ag', 'ai', 'ar', 'be', 'bl', 'bs', 'fr', 'ge', 'gl', 'gr', 'ju', 'lu',
        'ne', 'nw', 'ow', 'sg', 'sh', 'so', 'sz', 'tg', 'ti', 'ur', 'vd', 'vs',
        'zg', 'zh'
    }

    def __init__(
        self,
        name: str = '',
        logo: str = '',
        logo_for_pdf: str = '',
        color: str = '',
        canton: str | None = None,
        on_accept: dict[str, Any] | None = None,
        time_zone: str = 'Europe/Zurich',
        help_link: str = '',
        publishing: bool = False,
        frontend: bool = False,
        sogc_import: dict[str, Any] | None = None,
        links: dict[str, str] | None = None,
        **kwargs: object
    ) -> None:

        assert not canton or canton in self.CANTONS
        assert not on_accept or on_accept['mail_to']
        assert not frontend or (frontend and publishing)
        assert not links or isinstance(links, dict)
        assert not sogc_import or (
            sogc_import['endpoint']
            and sogc_import['category']
            and sogc_import['organization']
            and canton
        )

        self.canton = canton
        self.name = name
        self.logo = logo
        self.logo_for_pdf = logo_for_pdf
        self.color = color
        self.on_accept = on_accept or {}
        self.time_zone = time_zone
        self.help_link = help_link
        self.publishing = publishing
        self.frontend = frontend
        self.sogc_import = sogc_import or {}
        self.links = links
        if self.sogc_import and canton:
            self.sogc_import['canton'] = canton.upper()

    @classmethod
    def from_yaml(cls, yaml_source: str) -> Self:
        return cls(**safe_load(yaml_source))
