import time
import yaml

from pathlib import Path
from onegov.core.static import StaticFile


def load_sponsors(sponsors_path):
    root = Path(sponsors_path)

    with (root / 'sponsors.yml').open('r') as f:
        return [Sponsor(**sponsor) for sponsor in yaml.load(f)]


class Sponsor(object):

    __slots__ = (
        'name', 'logo', 'logo_url', 'mail_url', 'background', 'height',
        'width', 'top', 'banners'
    )

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def url_for(self, request, path):
        assert path.startswith('sponsors/')
        return request.link(StaticFile(path))

    def compiled(self, request, data=None):
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

        language = request.locale[:2]

        def translate(value):
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
