from __future__ import annotations

import time
import yaml

from pathlib import Path
from onegov.core.static import StaticFile


from typing import overload, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.feriennet.request import FeriennetRequest
    from typing import Self


def load_sponsors(sponsors_path: str) -> list[Sponsor]:
    root = Path(sponsors_path)

    with (root / 'sponsors.yml').open('r') as f:
        return [Sponsor(**sponsor) for sponsor in yaml.safe_load(f)]


# FIXME: This isn't particularly type safe, we should try to do better
class Sponsor:

    __slots__ = (
        'name', 'logo', 'logo_url', 'mail_url', 'background', 'height',
        'width', 'top', 'banners'
    )

    # FIXME: This is only true for a compiled sponsor, if we wanted to
    #        be type safe, then we should create a subclass for compiled
    #        sponsors which has this type set
    banners: dict[str, str]

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def url_for(self, request: FeriennetRequest, path: str) -> str:
        assert path.startswith('sponsors/')
        return request.link(StaticFile(path, version=request.app.version))

    @overload
    def compiled(
        self,
        request: FeriennetRequest,
        data: None = None
    ) -> Self: ...

    @overload
    def compiled(
        self,
        request: FeriennetRequest,
        data: dict[str, Any]
    ) -> dict[str, Any]: ...

    def compiled(
        self,
        request: FeriennetRequest,
        data: dict[str, Any] | None = None
    ) -> Self | dict[str, Any]:
        """ Returns an instance of the sponsor with all data localized and
        all variables replaced with the related values.

        This turns the following sponsor::

            url:
                de: Ja {timestamp}
                fr: Oui {timestamp}
                it: Si {timestamp}

        Into this::

            url: Ja

        """
        base = data is None
        data = data or {
            slot: getattr(self, slot, None) for slot in self.__slots__
        }

        assert request.locale is not None
        language = request.locale[:2]

        def translate(value: Any) -> Any:
            if isinstance(value, dict):
                if set(value.keys()) <= {'de', 'fr', 'it'}:
                    value = value[language]
                else:
                    return self.compiled(request, value)

            if isinstance(value, str):
                return value.format(timestamp=int(time.time() * 1000))

            return value

        translated = {
            key: translate(value) for key, value in data.items()
        }

        if base:
            return self.__class__(**translated)
        else:
            return translated
