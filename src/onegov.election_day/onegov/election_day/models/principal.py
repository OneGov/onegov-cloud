import onegov.election_day
import yaml

from datetime import date
from cached_property import cached_property
from collections import OrderedDict
from onegov.core import utils
from onegov.election_day import _
from pathlib import Path
from urllib.parse import urlsplit


cantons = {
    'ag', 'ai', 'ar', 'be', 'bl', 'bs', 'fr', 'ge', 'gl', 'gr', 'ju', 'lu',
    'ne', 'nw', 'ow', 'sg', 'sh', 'so', 'sz', 'tg', 'ti', 'ur', 'vd', 'vs',
    'zg', 'zh'
}


class Principal(object):
    """ The principal is the political entity running the election day app.

    If the principal is canton:
    * the ``canton`` shortcut must be set to a valid canton shortcut
      (e.g. ``be``)
    * the available domains are ``federation`` and ``canton``
    * use_maps is always true
    * ``muncipalities``/``entities`` returns the BFS numbers of the
      municipalties
    * there should be static data (BFS numbers and map data) for each canton
      for a bunch of years

    If the principal is a municipality:
    * the ``municipality`` shortcut must be set to a valid BFS number
      (e.g. ``351``)
    * the available domains are ``federation``, ``canton`` and ``municipality``
    * use_maps can be set to enable / display maps in the application
    * ``districts``/``entities`` returns the the districts of the muncipality,
      if there are any defined
    * there can optionally be static data (districts and map data)

    """

    def __init__(self, name, logo, color, canton=None, municipality=None,
                 base=None, analytics=None, use_maps=False, fetch=None,
                 webhooks=None, sms_notification=None):
        assert (
            (canton in cantons and municipality is None) or
            (canton is None and municipality is not None)
        )

        self.name = name
        self.logo = logo
        self.canton = canton
        self.municipality = municipality
        self.color = color
        self.base = base
        self.analytics = analytics
        self.use_maps = True if canton is not None else use_maps
        self.fetch = fetch or {}
        self.webhooks = webhooks or {}
        self.sms_notification = sms_notification

    @classmethod
    def from_yaml(cls, yaml_source):
        return cls(**yaml.load(yaml_source))

    @cached_property
    def base_domain(self):
        if self.base:
            return urlsplit(self.base).hostname.replace('www.', '')

    @cached_property
    def domain(self):
        """ the domain of influcence """
        if self.canton is not None:
            return 'canton'

        return 'municipality'

    @cached_property
    def id(self):
        """ the BFS code / district ID """
        return self.canton if self.domain == 'canton' else self.municipality

    @cached_property
    def available_domains(self):
        """ the usable domains of influence """
        result = OrderedDict()
        result['federation'] = _("federal")
        result['canton'] = _("cantonal")
        if self.domain == 'municipality':
            result['municipality'] = _("communal")
        return result

    @cached_property
    def municipalities(self):
        result = {}

        if self.domain == 'canton':
            path = utils.module_path(onegov.election_day,
                                     'static/municipalities')
            paths = (p for p in Path(path).iterdir() if p.is_dir())
            for path in paths:
                year = int(path.name)

                with (path / '{}.json'.format(self.canton)).open('r') as f:
                    result[year] = {int(k): v for k, v in yaml.load(f).items()}

        return result

    @cached_property
    def districts(self):
        result = {}

        if self.domain == 'municipality':
            path = utils.module_path(onegov.election_day, 'static/districts')
            paths = (p for p in Path(path).iterdir() if p.is_dir())
            for path in paths:
                year = int(path.name)

                path = path / '{}.json'.format(self.municipality)
                if path.exists():
                    with (path).open('r') as f:
                        result[year] = {
                            int(k): v for k, v in yaml.load(f).items()
                        }

            if not result:
                result = {
                    year: {int(self.id): {'name': self.name}}
                    for year in range(2009, date.today().year + 2)
                }

        return result

    @cached_property
    def entities(self):
        return self.municipalities or self.districts

    def is_year_available(self, year, map_required=True):
        if self.entities and year not in self.entities:
            return False

        if map_required:
            path = utils.module_path(onegov.election_day, 'static/mapdata')
            name = self.canton or self.municipality
            return Path('{}/{}/{}.json'.format(path, year, name)).exists()

        return True

    @cached_property
    def notifications(self):
        if (len(self.webhooks) > 0) or self.sms_notification:
            return True
        return False
