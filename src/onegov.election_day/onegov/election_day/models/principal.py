import onegov.election_day
import yaml

from cached_property import cached_property
from onegov.core import utils
from pathlib import Path
from urllib.parse import urlsplit


cantons = {
    'ag', 'ai', 'ar', 'be', 'bl', 'bs', 'fr', 'ge', 'gl', 'gr', 'ju', 'lu',
    'ne', 'nw', 'ow', 'sg', 'sh', 'so', 'sz', 'tg', 'ti', 'ur', 'vd', 'vs',
    'zg', 'zh'
}


class Principal(object):
    """ The principal is the town or municipality running the election day app.

    """

    def __init__(self, name, logo, canton, color, base=None, analytics=None):
        assert canton in cantons

        self.name = name
        self.logo = logo
        self.canton = canton
        self.color = color
        self.base = base
        self.analytics = analytics

    @classmethod
    def from_yaml(cls, yaml_source):
        return cls(**yaml.load(yaml_source))

    @cached_property
    def base_domain(self):
        if self.base:
            return urlsplit(self.base).hostname.replace('www.', '')

    @cached_property
    def municipalities(self):
        path = utils.module_path(onegov.election_day, 'static/municipalities')
        paths = (p for p in Path(path).iterdir() if p.is_dir())

        result = {}

        for path in paths:
            year = int(path.name)

            with (path / '{}.json'.format(self.canton)).open('r') as f:
                result[year] = {int(k): v for k, v in yaml.load(f).items()}

        return result

    def is_year_available(self, year, map_required=True):
        if year not in self.municipalities:
            return False

        if map_required:
            path = utils.module_path(onegov.election_day, 'static/mapdata')
            return Path('{}/{}'.format(path, year)).is_dir()

        return True
