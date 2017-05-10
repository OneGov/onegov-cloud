import yaml

from pathlib import Path
from onegov.core.static import StaticFile


def load_sponsors(sponsors_path):
    root = Path(sponsors_path)

    with (root / 'sponsors.yml').open('r') as f:
        return [Sponsor(**sponsor) for sponsor in yaml.load(f)]


class Sponsor(object):

    __slots__ = (
        'name', 'logo', 'link', 'background', 'height', 'width', 'top'
    )

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def logo_path(self, request):
        return request.link(StaticFile(self.logo))
