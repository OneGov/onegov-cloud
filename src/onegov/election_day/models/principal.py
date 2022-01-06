import onegov.election_day

from cached_property import cached_property
from collections import OrderedDict
from datetime import date
from onegov.core import utils
from onegov.core.custom import json
from onegov.election_day import _
from pathlib import Path
from urllib.parse import urlsplit
from yaml import safe_load


class Principal(object):
    """ The principal is the political entity running the election day app.

    There are currently two different types of principals supported: Cantons
    and Municipalitites.

    A principal is identitifed by its ID (municipalitites: BFS number, cantons:
    canton code).

    A principal may consist of different entitites (municipalitites: quarters,
    cantons: municipalities) grouped by districts. Some cantons have regions
    for certain years, an additional type of district only used for regional
    elections (Kantonsratswahl, Grossratswahl, Landratswahl). Some of them have
    superregions which further aggregate these regions. The label of the
    entity, the districts, regions and superregions may vary and can be queried
    with `label`.

    A principal is part of a domain (municipalitites: municipality, canton:
    canton) and supports different types of domains (typically all higher
    domains).

    hidden_elements: Used to optionally show and hide certain charts on
    the defined views.

    Example config in a yaml file::

        hidden_elements:
          always:
            candidate-by-entity:
              chart_percentages: true
          intermediate_results:
            connections:
              chart: false
            candidates:
              chart: false

    publish_intermediate_results: Optionally renders svg and pdf for
    intermediate results. Example::

        publish_intermediate_results:
          vote: true
          election: true
          election_compound: true

    Defaults to false if nothing specified

    """

    def __init__(
        self,
        id_=None,
        domain=None,
        domains_election=None,
        domains_vote=None,
        entities=None,
        name=None,
        logo=None,
        logo_position='left',
        color='#000',
        base=None,
        analytics=None,
        has_districts=True,
        has_regions=False,
        has_superregions=False,
        use_maps=False,
        fetch=None,
        webhooks=None,
        sms_notification=None,
        email_notification=None,
        wabsti_import=False,
        pdf_signing=None,
        open_data=None,
        hidden_elements=None,
        publish_intermediate_results=None,
        csp_script_src=None,
        csp_connect_src=None,
        cache_expiration_time=300,
        reply_to=None,
        custom_css=None,
        **kwargs
    ):
        assert all((id_, domain, domains_election, domains_vote, entities))
        self.id = id_
        self.domain = domain
        self.domains_election = domains_election
        self.domains_vote = domains_vote
        self.entities = entities
        self.name = name
        self.logo = logo
        self.logo_position = logo_position
        self.color = color
        self.base = base
        self.analytics = analytics
        self.has_districts = has_districts
        self.has_regions = has_regions
        self.has_superregions = has_superregions
        self.use_maps = use_maps
        self.fetch = fetch or {}
        self.webhooks = webhooks or {}
        self.sms_notification = sms_notification
        self.email_notification = email_notification
        self.wabsti_import = wabsti_import
        self.pdf_signing = pdf_signing or {}
        self.open_data = open_data or {}
        self.hidden_elements = hidden_elements or {}
        self.publish_intermediate_results = publish_intermediate_results or {
            'vote': False,
            'election': False,
            'election_compound': False
        }
        self.csp_script_src = csp_script_src or []
        self.csp_connect_src = csp_connect_src or []
        self.cache_expiration_time = cache_expiration_time
        self.reply_to = reply_to
        self.custom_css = custom_css

    @classmethod
    def from_yaml(cls, yaml_source):
        kwargs = safe_load(yaml_source)
        assert 'canton' in kwargs or 'municipality' in kwargs
        assert not ('canton' in kwargs and 'municipality' in kwargs)
        if 'canton' in kwargs:
            return Canton(**kwargs)
        else:
            return Municipality(**kwargs)

    @cached_property
    def base_domain(self):
        if self.base:
            return urlsplit(self.base).hostname.replace('www.', '')

    def is_year_available(self, year, map_required=True):
        if self.entities and year not in self.entities:
            return False

        if map_required:
            path = utils.module_path(onegov.election_day, 'static/mapdata')
            return Path(
                '{}/{}/{}.json'.format(path, year, self.id)
            ).exists()

        return True

    @cached_property
    def notifications(self):
        if (
            (len(self.webhooks) > 0)
            or self.sms_notification
            or self.email_notification
        ):
            return True
        return False

    def label(self, value):
        raise NotImplementedError()

    @cached_property
    def hidden_tabs(self):
        return self.hidden_elements.get('tabs', {})


class Canton(Principal):
    """ A cantonal instance. """

    CANTONS = {
        'ag', 'ai', 'ar', 'be', 'bl', 'bs', 'fr', 'ge', 'gl', 'gr', 'ju', 'lu',
        'ne', 'nw', 'ow', 'sg', 'sh', 'so', 'sz', 'tg', 'ti', 'ur', 'vd', 'vs',
        'zg', 'zh'
    }

    def __init__(self, canton=None, **kwargs):
        assert canton in self.CANTONS

        kwargs.pop('use_maps', None)

        domains_election = OrderedDict((
            ('federation', _("Federal")),
            ('region', _("Regional")),
            ('canton', _("Cantonal"))
        ))
        domains_vote = OrderedDict((
            ('federation', _("Federal")),
            ('canton', _("Cantonal"))
        ))

        # Read the municipalties for each year from our static data
        entities = {}
        path = utils.module_path(onegov.election_day, 'static/municipalities')
        paths = (p for p in Path(path).iterdir() if p.is_dir())
        for path in paths:
            year = int(path.name)
            with (path / '{}.json'.format(canton)).open('r') as f:
                entities[year] = {int(k): v for k, v in json.load(f).items()}

        # Test if all entities have districts (use none, if ambiguous)
        districts = set([
            entity.get('district', None)
            for year in entities.values()
            for entity in year.values()
        ])
        has_districts = None not in districts

        # Test if some of the entities have regions
        regions = set([
            entity.get('region', None)
            for year in entities.values()
            for entity in year.values()
        ])
        has_regions = regions != {None}

        # Test if some of the entities have superregions
        superregions = set([
            entity.get('superregion', None)
            for year in entities.values()
            for entity in year.values()
        ])
        has_superregions = superregions != {None}

        super(Canton, self).__init__(
            id_=canton,
            domain='canton',
            domains_election=domains_election,
            domains_vote=domains_vote,
            entities=entities,
            has_districts=has_districts,
            has_regions=has_regions,
            has_superregions=has_superregions,
            use_maps=True,
            **kwargs
        )

    def label(self, value):
        if value == 'entity':
            return _("Municipality")
        if value == 'entities':
            return _("Municipalities")
        if value == 'district':
            if self.id == 'bl':
                return _("district_label_bl")
            if self.id == 'gr':
                return _("district_label_gr")
            if self.id == 'sz':
                return _("district_label_sz")
            return _("District")
        if value == 'districts':
            if self.id == 'bl':
                return _("districts_label_bl")
            if self.id == 'gr':
                return _("districts_label_gr")
            if self.id == 'sz':
                return _("districts_label_sz")
            return _("Districts")
        if value == 'region':
            if self.id in ('sz', 'zg'):
                return _("Municipality")
            return _("District")
        if value == 'regions':
            if self.id in ('sz', 'zg'):
                return _("Municipalities")
            return _("Districts")
        if value == 'superregion':
            if self.id == 'bl':
                # Region
                return _("superregion_label_bl")
            return _("District")
        if value == 'superregions':
            if self.id == 'bl':
                # Regionen
                return _("superregions_label_bl")
            return _("Districts")
        return ''


class Municipality(Principal):
    """ A communal instance. """

    def __init__(self, municipality=None, **kwargs):
        assert municipality
        domains = OrderedDict((
            ('federation', _("Federal")),
            ('canton', _("Cantonal")),
            ('municipality', _("Communal"))
        ))

        # Try to read the quarters for each year from our static data
        entities = {}
        path = utils.module_path(onegov.election_day, 'static/quarters')
        paths = (p for p in Path(path).iterdir() if p.is_dir())
        for path in paths:
            year = int(path.name)
            path = path / '{}.json'.format(municipality)
            if path.exists():
                with (path).open('r') as f:
                    entities[year] = {
                        int(k): v for k, v in json.load(f).items()
                    }
        if entities:
            self.has_quarters = True
            # Test if all entities have districts (use none, if ambiguous)
            districts = set([
                entity.get('district', None)
                for year in entities.values()
                for entity in year.values()
            ])
            has_districts = None not in districts
        else:
            # ... we have no static data, autogenerate it!
            self.has_quarters = False
            has_districts = False
            entities = {
                year: {int(municipality): {'name': kwargs.get('name', '')}}
                for year in range(2002, date.today().year + 1)
            }

        super(Municipality, self).__init__(
            id_=municipality,
            domain='municipality',
            domains_election=domains,
            domains_vote=domains,
            entities=entities,
            has_districts=has_districts,
            **kwargs
        )

    def label(self, value):
        if value == 'entity':
            return _("Quarter") if self.has_quarters else _("Municipality")
        if value == 'entities':
            return _("Quarters") if self.has_quarters else _("Municipalities")
        return ''
