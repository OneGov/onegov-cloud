from __future__ import annotations

import onegov.election_day

from functools import cached_property
from collections import OrderedDict
from datetime import date
from markupsafe import Markup
from onegov.core import utils
from onegov.core.custom import json
from onegov.core.custom import msgpack
from onegov.election_day import _, log
from pathlib import Path
from urllib.parse import urlsplit
from yaml import safe_load


from typing import Any
from typing import Literal
from typing import Self
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from translationstring import TranslationString
    from typing import Never
    from yaml.reader import _ReadStream


class Principal:
    """ The principal is the political entity running the election day app.

    There are currently two different types of principals supported: Cantons
    and Municipalitites.

    A principal is identitifed by its ID (municipalitites: BFS number, cantons:
    canton code).

    A principal may consist of different entities (municipalitites: quarters,
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
        id_: str,
        domain: str,
        domains_election: dict[str, TranslationString],
        domains_vote: dict[str, TranslationString],
        entities: dict[int, dict[int, dict[str, str]]],
        name: str | None = None,
        logo: str | None = None,
        logo_position: str = 'left',
        color: str = '#000',
        base: str | None = None,
        analytics: str | None = None,
        has_districts: bool = True,
        has_regions: bool = False,
        has_superregions: bool = False,
        use_maps: bool = False,
        fetch: dict[str, Any] | None = None,
        webhooks: dict[str, dict[str, str]] | None = None,
        sms_notification: str | None = None,
        email_notification: bool | None = None,
        wabsti_import: bool = False,
        open_data: dict[str, str] | None = None,
        hidden_elements: dict[str, dict[str, dict[str, bool]]] | None = None,
        publish_intermediate_results: dict[str, bool] | None = None,
        csp_script_src: list[str] | None = None,
        csp_connect_src: list[str] | None = None,
        cache_expiration_time: int = 300,
        reply_to: str | None = None,
        custom_css: str | None = None,
        official_host: str | None = None,
        segmented_notifications: bool = False,
        private: bool = False,
        **kwargs: Never
    ):
        assert all((id_, domain, domains_election, domains_vote, entities))
        self.id = id_
        self.domain = domain
        self.domains_election = domains_election
        self.domains_vote = domains_vote
        self.entities = entities
        self.name = name or id_
        self.logo = logo
        self.logo_position = logo_position
        self.color = color
        self.base = base
        # NOTE: This is inherently unsafe, since we need to allow script tags
        #       in order for most analytics to work. Eventually this may be
        #       able to go away again or be reduced to support a few specific
        #       providers.
        self.analytics = Markup(analytics) if analytics else None  # nosec: B704
        self.has_districts = has_districts
        self.has_regions = has_regions
        self.has_superregions = has_superregions
        self.use_maps = use_maps
        self.fetch = fetch or {}
        self.webhooks = webhooks or {}
        self.sms_notification = sms_notification
        self.email_notification = email_notification
        self.wabsti_import = wabsti_import
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
        self.official_host = official_host
        self.segmented_notifications = segmented_notifications
        self.private = private

    @classmethod
    def from_yaml(cls, yaml_source: _ReadStream) -> Canton | Municipality:
        kwargs = safe_load(yaml_source)
        assert 'canton' in kwargs or 'municipality' in kwargs
        if 'municipality' in kwargs:
            return Municipality(**kwargs)
        else:
            return Canton(**kwargs)

    @cached_property
    def base_domain(self) -> str | None:
        if not self.base:
            return None

        hostname = urlsplit(self.base).hostname
        if hostname is None:
            return None
        return hostname.replace('www.', '')

    def is_year_available(self, year: int, map_required: bool = True) -> bool:
        if self.entities and year not in self.entities:
            return False

        if map_required:
            path = utils.module_path(onegov.election_day, 'static/mapdata')
            return Path(
                '{}/{}/{}.json'.format(path, year, self.id)
            ).exists()

        return True

    def get_entities(self, year: int) -> set[str]:
        entities = {
            entity.get('name', None)
            for entity in self.entities.get(year, {}).values()
        }
        return {entity for entity in entities if entity}

    def get_districts(self, year: int) -> set[str]:
        if self.has_districts:
            districts = {
                entity.get('district', None)
                for entity in self.entities.get(year, {}).values()
            }
            return {district for district in districts if district}
        return set()

    def get_regions(self, year: int) -> set[str]:
        if self.has_regions:
            regions = {
                entity.get('region', None)
                for entity in self.entities.get(year, {}).values()
            }
            return {region for region in regions if region}
        return set()

    def get_superregion(self, region: str, year: int) -> str:
        if self.has_superregions:
            for entity in self.entities.get(year, {}).values():
                if entity.get('region') == region:
                    return entity.get('superregion', '')
        return ''

    def get_superregions(self, year: int) -> set[str]:
        if self.has_superregions:
            superregions = {
                entity.get('superregion', None)
                for entity in self.entities.get(year, {}).values()
            }
            return {superregion for superregion in superregions if superregion}
        return set()

    def label(self, value: str) -> str:
        raise NotImplementedError()


class Canton(Principal, msgpack.Serializable, tag=50, keys=(
    'canton',
    'domains_election',
    'domains_vote',
    'entities',
    'name',
    'logo',
    'logo_position',
    'color',
    'base',
    'analytics',
    'has_districts',
    'has_regions',
    'has_superregions',
    'fetch',
    'webhooks',
    'sms_notification',
    'email_notification',
    'wabsti_import',
    'open_data',
    'hidden_elements',
    'publish_intermediate_results',
    'csp_script_src',
    'csp_connect_src',
    'cache_expiration_time',
    'reply_to',
    'custom_css',
    'official_host',
    'segmented_notifications',
    'private',
)):
    """ A cantonal instance. """

    CANTONS = {
        'zh': 1,
        'be': 2,
        'lu': 3,
        'ur': 4,
        'sz': 5,
        'ow': 6,
        'nw': 7,
        'gl': 8,
        'zg': 9,
        'fr': 10,
        'so': 11,
        'bs': 12,
        'bl': 13,
        'sh': 14,
        'ar': 15,
        'ai': 16,
        'sg': 17,
        'gr': 18,
        'ag': 19,
        'tg': 20,
        'ti': 21,
        'vd': 22,
        'vs': 23,
        'ne': 24,
        'ge': 25,
        'ju': 26,
    }

    domain: Literal['canton']

    def __init__(self, canton: str, **kwargs: Any) -> None:
        assert canton in self.CANTONS

        self.canton = canton

        kwargs.pop('use_maps', None)

        # Read the municipalties for each year from our static data
        entities = {}
        basedir = utils.module_path(
            onegov.election_day,
            'static/municipalities'
        )
        paths = (p for p in Path(basedir).iterdir() if p.is_dir())
        for path in paths:
            year = int(path.name)
            with (path / '{}.json'.format(canton)).open('r') as f:
                entities[year] = {int(k): v for k, v in json.load(f).items()}

        # NOTE: this section may depend on static data for principle.entities.
        # See src/onegov/election_day/static/municipalities/<year>/*.json
        if date.today().year not in entities:
            log.warning(
                f'Warning: No entities for year {date.today().year} found '
                f'for {canton}'
            )

        # Test if all entities have districts (use none, if ambiguous)
        districts = {
            entity.get('district', None)
            for year in entities.values()
            for entity in year.values()
        }
        has_districts = None not in districts

        # Test if some of the entities have regions
        regions = {
            entity.get('region', None)
            for year in entities.values()
            for entity in year.values()
        }
        has_regions = regions != {None}

        # Test if some of the entities have superregions
        superregions = {
            entity.get('superregion', None)
            for year in entities.values()
            for entity in year.values()
        }
        has_superregions = superregions != {None}

        domains_election: dict[str, TranslationString] = OrderedDict()
        domains_election['federation'] = _('Federal')
        domains_election['canton'] = _('Cantonal')
        if has_regions:
            domains_election['region'] = _(
                'Regional (${on})',
                mapping={'on': self.label('region')}
            )
        if has_districts:
            domains_election['district'] = _(
                'Regional (${on})',
                mapping={'on': self.label('district')}
            )
        domains_election['none'] = _(
            'Regional (${on})',
            mapping={'on': _('Other')}
        )
        domains_election['municipality'] = _('Communal')

        domains_vote: dict[str, TranslationString] = OrderedDict()
        domains_vote['federation'] = _('Federal')
        domains_vote['canton'] = _('Cantonal')
        domains_vote['municipality'] = _('Communal')

        super().__init__(
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

    @classmethod
    def from_dict(
        cls,
        canton: str,
        domains_election: dict[str, TranslationString],
        domains_vote: dict[str, TranslationString],
        entities: dict[int, dict[int, dict[str, str]]],
        name: str | None = None,
        logo: str | None = None,
        logo_position: str = 'left',
        color: str = '#000',
        base: str | None = None,
        analytics: str | None = None,
        has_districts: bool = True,
        has_regions: bool = False,
        has_superregions: bool = False,
        fetch: dict[str, Any] | None = None,
        webhooks: dict[str, dict[str, str]] | None = None,
        sms_notification: str | None = None,
        email_notification: bool | None = None,
        wabsti_import: bool = False,
        open_data: dict[str, str] | None = None,
        hidden_elements: dict[str, dict[str, dict[str, bool]]] | None = None,
        publish_intermediate_results: dict[str, bool] | None = None,
        csp_script_src: list[str] | None = None,
        csp_connect_src: list[str] | None = None,
        cache_expiration_time: int = 300,
        reply_to: str | None = None,
        custom_css: str | None = None,
        official_host: str | None = None,
        segmented_notifications: bool = False,
        private: bool = False,
        **kwargs: Never,
    ) -> Self:

        assert canton in cls.CANTONS

        self = object.__new__(cls)
        self.canton = canton

        Principal.__init__(
            self,
            id_=canton,
            domain='canton',
            domains_election=domains_election,
            domains_vote=domains_vote,
            entities=entities,
            name=name,
            logo=logo,
            logo_position=logo_position,
            color=color,
            base=base,
            analytics=analytics,
            has_districts=has_districts,
            has_regions=has_regions,
            has_superregions=has_superregions,
            use_maps=True,
            fetch=fetch,
            webhooks=webhooks,
            sms_notification=sms_notification,
            email_notification=email_notification,
            wabsti_import=wabsti_import,
            open_data=open_data,
            hidden_elements=hidden_elements,
            publish_intermediate_results=publish_intermediate_results,
            csp_script_src=csp_script_src,
            csp_connect_src=csp_connect_src,
            cache_expiration_time=cache_expiration_time,
            reply_to=reply_to,
            custom_css=custom_css,
            official_host=official_host,
            segmented_notifications=segmented_notifications,
            private=private,
        )

        return self

    def label(self, value: str) -> str:
        if value == 'entity':
            return _('Municipality')
        if value == 'entities':
            return _('Municipalities')
        if value == 'district':
            if self.canton == 'bl':
                return _('district_label_bl')
            if self.canton == 'gr':
                return _('district_label_gr')
            if self.canton == 'sz':
                return _('district_label_sz')
            return _('District')
        if value == 'districts':
            if self.canton == 'bl':
                return _('districts_label_bl')
            if self.canton == 'gr':
                return _('districts_label_gr')
            if self.canton == 'sz':
                return _('districts_label_sz')
            return _('Districts')
        if value == 'region':
            if self.canton == 'gr':
                return _('region_label_gr')
            return _('District')
        if value == 'regions':
            if self.canton == 'gr':
                return _('regions_label_gr')
            return _('Districts')
        if value == 'superregion':
            if self.canton == 'bl':
                return _('superregion_label_bl')
            return _('District')
        if value == 'superregions':
            if self.canton == 'bl':
                return _('superregions_label_bl')
            return _('Districts')
        if value == 'mandates':
            if self.canton == 'gr':
                return _('Seats')
            return _('Mandates')
        return ''


class Municipality(Principal, msgpack.Serializable, tag=51, keys=(
    'municipality',
    'canton',
    'canton_name',
    'domains_election',
    'domains_vote',
    'entities',
    'name',
    'logo',
    'logo_position',
    'color',
    'base',
    'analytics',
    'has_districts',
    'has_regions',
    'has_superregions',
    'has_quarters',
    'use_maps',
    'fetch',
    'webhooks',
    'sms_notification',
    'email_notification',
    'wabsti_import',
    'open_data',
    'hidden_elements',
    'publish_intermediate_results',
    'csp_script_src',
    'csp_connect_src',
    'cache_expiration_time',
    'reply_to',
    'custom_css',
    'official_host',
    'private',
)):
    """ A communal instance. """

    domain: Literal['municipality']

    def __init__(
        self,
        municipality: str,
        canton: str,
        canton_name: str,
        **kwargs: Any
    ) -> None:
        assert municipality and canton and canton_name

        self.municipality = municipality
        self.canton = canton
        self.canton_name = canton_name

        kwargs.pop('segmented_notifications', None)

        domains: dict[str, TranslationString] = OrderedDict((
            ('federation', _('Federal')),
            ('canton', _('Cantonal')),
            ('municipality', _('Communal'))
        ))

        # Try to read the quarters for each year from our static data
        entities = {}
        basedir = utils.module_path(onegov.election_day, 'static/quarters')
        paths = (p for p in Path(basedir).iterdir() if p.is_dir())
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
            districts = {
                entity.get('district', None)
                for year in entities.values()
                for entity in year.values()
            }
            has_districts = None not in districts
        else:
            # ... we have no static data, autogenerate it!
            self.has_quarters = False
            has_districts = False
            entities = {
                year: {int(municipality): {'name': kwargs.get('name', '')}}
                for year in range(2002, date.today().year + 1)
            }

        # NOTE: this section may depend on static data for principle.entities.
        # See src/onegov/election_day/static/municipalities/<year>/*.json
        if date.today().year not in entities:
            log.warning(
                f'Warning: No entities for year {date.today().year} found '
                f'for {municipality}'
            )

        super().__init__(
            id_=municipality,
            domain='municipality',
            domains_election=domains,
            domains_vote=domains,
            entities=entities,
            has_districts=has_districts,
            **kwargs
        )

    @classmethod
    def from_dict(
        cls,
        municipality: str,
        canton: str,
        canton_name: str,
        domains_election: dict[str, TranslationString],
        domains_vote: dict[str, TranslationString],
        entities: dict[int, dict[int, dict[str, str]]],
        name: str | None = None,
        logo: str | None = None,
        logo_position: str = 'left',
        color: str = '#000',
        base: str | None = None,
        analytics: str | None = None,
        has_districts: bool = True,
        has_regions: bool = False,
        has_superregions: bool = False,
        has_quarters: bool = False,
        use_maps: bool = False,
        fetch: dict[str, Any] | None = None,
        webhooks: dict[str, dict[str, str]] | None = None,
        sms_notification: str | None = None,
        email_notification: bool | None = None,
        wabsti_import: bool = False,
        open_data: dict[str, str] | None = None,
        hidden_elements: dict[str, dict[str, dict[str, bool]]] | None = None,
        publish_intermediate_results: dict[str, bool] | None = None,
        csp_script_src: list[str] | None = None,
        csp_connect_src: list[str] | None = None,
        cache_expiration_time: int = 300,
        reply_to: str | None = None,
        custom_css: str | None = None,
        official_host: str | None = None,
        private: bool = False,
        **kwargs: Never,
    ) -> Self:

        assert municipality and canton and canton_name
        self = object.__new__(cls)

        self.municipality = municipality
        self.canton = canton
        self.canton_name = canton_name
        self.has_quarters = has_quarters

        Principal.__init__(
            self,
            id_=municipality,
            domain='municipality',
            domains_election=domains_election,
            domains_vote=domains_vote,
            entities=entities,
            name=name,
            logo=logo,
            logo_position=logo_position,
            color=color,
            base=base,
            analytics=analytics,
            has_districts=has_districts,
            has_regions=has_regions,
            has_superregions=has_superregions,
            use_maps=use_maps,
            fetch=fetch,
            webhooks=webhooks,
            sms_notification=sms_notification,
            email_notification=email_notification,
            wabsti_import=wabsti_import,
            open_data=open_data,
            hidden_elements=hidden_elements,
            publish_intermediate_results=publish_intermediate_results,
            csp_script_src=csp_script_src,
            csp_connect_src=csp_connect_src,
            cache_expiration_time=cache_expiration_time,
            reply_to=reply_to,
            custom_css=custom_css,
            official_host=official_host,
            private=private,
        )

        return self

    def label(self, value: str) -> str:
        if value == 'entity':
            return _('Quarter') if self.has_quarters else _('Municipality')
        if value == 'entities':
            return _('Quarters') if self.has_quarters else _('Municipalities')
        return ''
