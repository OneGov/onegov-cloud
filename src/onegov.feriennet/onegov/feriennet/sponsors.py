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

    def localized(self, request, data=None):
        """ Returns an instance of the sponsor with all localisation structures
        localized according to the current language.

        This turns the following sponsor::

            url:
                de: Ja
                fr: Oui
                it: Si

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
                    return value[language]
                return self.localized(request, value)

            return value

        translated = {
            key: translate(value) for key, value in data.items()
        }

        if base:
            return self.__class__(**translated)
        else:
            return translated
