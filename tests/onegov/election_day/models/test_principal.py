from __future__ import annotations

from freezegun import freeze_time
from onegov.election_day.models import Canton
from onegov.election_day.models import Municipality
from onegov.election_day.models import Principal
from textwrap import dedent


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from ..conftest import TestApp


SUPPORTED_YEARS = list(range(2002, 2025 + 1))

SUPPORTED_YEARS_MAP = list(range(2013, 2025 + 1))
SUPPORTED_YEARS_NO_MAP = list(set(SUPPORTED_YEARS) - set(SUPPORTED_YEARS_MAP))

SUPPORTED_YEARS_MAP_ADDITIONAL = list(range(2004, 2025 + 1))
SUPPORTED_YEARS_NO_MAP_ADDITIONAL = list(
    set(SUPPORTED_YEARS) - set(SUPPORTED_YEARS_MAP_ADDITIONAL)
)


def test_principal_load() -> None:
    # Canton with minimal options
    principal = Principal.from_yaml(dedent("""
        name: Kanton Zug
        canton: zg
    """))

    assert isinstance(principal, Canton)
    assert principal.name == 'Kanton Zug'
    assert principal.id == 'zg'
    assert principal.domain == 'canton'
    assert list(principal.domains_election.keys()) == [
        'federation', 'canton', 'none', 'municipality'
    ]
    assert list(principal.domains_vote.keys()) == [
        'federation', 'canton', 'municipality'
    ]
    assert len(principal.entities)
    assert len(list(principal.entities.values())[0])

    assert principal.logo is None
    assert principal.color == '#000'
    assert principal.base is None
    assert principal.base_domain is None
    assert principal.analytics is None
    assert principal.use_maps is True
    assert principal.has_districts is False
    assert principal.fetch == {}
    assert principal.webhooks == {}
    assert principal.sms_notification is None
    assert principal.email_notification is None
    assert principal.wabsti_import is False
    assert principal.open_data == {}
    assert principal.hidden_elements == {}
    assert principal.publish_intermediate_results == {
        'vote': False, 'election': False, 'election_compound': False
    }

    # Canton with all options
    principal = Principal.from_yaml(dedent("""
        name: Kanton Zug
        canton: zg
        base: 'http://www.zg.ch'
        analytics: "<script type=\\"text/javascript\\"></script>"
        use_maps: false
        wabsti_import: true
        fetch:
            steinhausen:
                - municipality
            baar:
                - municipality
        webhooks:
            'https://example.org/1':
            'https://example.org/2':
                My-Header: My-Value
        sms_notification: 'https://wab.zg.ch'
        email_notification: true
        open_data:
            id: kanton-zug
            name: Staatskanzlei Kanton Zug
            mail: info@zg.ch
        hidden_elements:
          always:
            candidate-by-entity:
              percentages: True
          intermediate_results:
            connections:
              chart: True
    """))
    assert isinstance(principal, Canton)
    assert principal.id == 'zg'
    assert principal.domain == 'canton'
    assert principal.name == 'Kanton Zug'
    assert principal.logo is None
    assert principal.color == '#000'
    assert principal.base == 'http://www.zg.ch'
    assert principal.base_domain == 'zg.ch'
    assert principal.analytics == '<script type="text/javascript"></script>'
    assert principal.use_maps is True
    assert principal.has_districts is False
    assert principal.fetch == {
        'steinhausen': ['municipality'],
        'baar': ['municipality']
    }
    assert principal.webhooks == {
        'https://example.org/1': None,
        'https://example.org/2': {
            'My-Header': 'My-Value'
        }
    }
    assert principal.sms_notification == 'https://wab.zg.ch'
    assert principal.email_notification is True
    assert principal.wabsti_import is True
    assert principal.open_data == {
        'id': 'kanton-zug',
        'name': 'Staatskanzlei Kanton Zug',
        'mail': 'info@zg.ch'
    }

    assert principal.hidden_elements == {
        'always': {
            'candidate-by-entity': {'percentages': True}
        },
        'intermediate_results': {
            'connections': {'chart': True}
        },
    }

    # Municipality with static data
    principal = Principal.from_yaml(dedent("""
        name: Stadt Bern
        canton: be
        canton_name: Kanton Bern
        municipality: '351'
    """))
    assert isinstance(principal, Municipality)
    assert principal.name == 'Stadt Bern'
    assert principal.id == '351'
    assert principal.canton == 'be'
    assert principal.canton_name == 'Kanton Bern'
    assert principal.domain == 'municipality'
    assert list(principal.domains_election.keys()) == [
        'federation', 'canton', 'municipality'
    ]
    assert list(principal.domains_vote.keys()) == [
        'federation', 'canton', 'municipality'
    ]
    assert principal.has_quarters is True
    assert len(principal.entities)
    assert len(list(principal.entities.values())[0])

    assert principal.logo is None
    assert principal.color == '#000'
    assert principal.base is None
    assert principal.base_domain is None
    assert principal.analytics is None
    assert principal.use_maps is False
    assert principal.has_districts is False
    assert principal.fetch == {}
    assert principal.webhooks == {}
    assert principal.sms_notification is None
    assert principal.email_notification is None
    assert principal.wabsti_import is False

    # Municipality without static data
    principal = Principal.from_yaml(dedent("""
        name: Kriens
        municipality: '1059'
        canton: lu
        canton_name: Kanton Luzern
    """))
    assert isinstance(principal, Municipality)
    assert principal.name == 'Kriens'
    assert principal.id == '1059'
    assert principal.canton == 'lu'
    assert principal.canton_name == 'Kanton Luzern'
    assert principal.domain == 'municipality'
    assert list(principal.domains_election.keys()) == [
        'federation', 'canton', 'municipality'
    ]
    assert list(principal.domains_vote.keys()) == [
        'federation', 'canton', 'municipality'
    ]
    assert principal.has_quarters is False
    assert len(principal.entities)
    assert len(list(principal.entities.values())[0]) == 1

    assert principal.logo is None
    assert principal.color == '#000'
    assert principal.base is None
    assert principal.base_domain is None
    assert principal.analytics is None
    assert principal.use_maps is False
    assert principal.has_districts is False
    assert principal.fetch == {}
    assert principal.webhooks == {}
    assert principal.sms_notification is None
    assert principal.email_notification is None
    assert principal.wabsti_import is False


def test_canton() -> None:
    # All cantons
    for canton_name in Canton.CANTONS:
        principal = Canton(name=canton_name, canton=canton_name)
        for year in SUPPORTED_YEARS:
            assert principal.entities[year]

    # BL
    canton = Canton(name='bl', canton='bl')
    assert canton.has_districts is True
    assert canton.has_regions is True
    assert canton.has_superregions is True
    assert list(canton.domains_election.keys()) == [
        'federation', 'canton', 'region', 'district', 'none', 'municipality'
    ]
    assert canton.get_entities(2022)
    assert canton.get_districts(2022)
    assert canton.get_regions(2022)
    assert canton.get_superregions(2022)
    assert canton.get_superregion('Pratteln', 1900) == ''
    assert canton.get_superregion('Basel', 2021) == ''
    assert canton.get_superregion('Pratteln', 2021) == 'Region 3'
    assert canton.get_superregion('Reinach', 2022) == 'Region 2'

    # GR
    canton = Canton(name='gr', canton='gr')
    assert canton.has_districts is True
    assert canton.has_regions is True
    assert canton.has_superregions is False
    assert list(canton.domains_election.keys()) == [
        'federation', 'canton', 'region', 'district', 'none', 'municipality'
    ]
    assert canton.get_entities(2022)
    assert canton.get_districts(2022)
    assert canton.get_regions(2022)
    assert not canton.get_superregions(2022)

    # SG
    canton = Canton(name='sg', canton='sg')
    assert canton.has_districts is True
    assert canton.has_regions is False
    assert canton.has_superregions is False
    assert list(canton.domains_election.keys()) == [
        'federation', 'canton', 'district', 'none', 'municipality'
    ]
    assert canton.get_entities(2022)
    assert canton.get_districts(2022)
    assert not canton.get_regions(2022)
    assert not canton.get_superregions(2022)

    # SZ
    canton = Canton(name='sz', canton='sz')
    assert canton.has_districts is True
    assert canton.has_regions is False
    assert canton.has_superregions is False
    assert list(canton.domains_election.keys()) == [
        'federation', 'canton', 'district', 'none', 'municipality'
    ]
    assert canton.get_entities(2022)
    assert canton.get_districts(2022)
    assert not canton.get_regions(2022)
    assert not canton.get_superregions(2022)

    # ZG
    canton = Canton(name='zg', canton='zg')
    assert canton.has_districts is False
    assert canton.has_regions is False
    assert canton.has_superregions is False
    assert list(canton.domains_election.keys()) == [
        'federation', 'canton', 'none', 'municipality'
    ]
    assert canton.get_entities(2022)
    assert not canton.get_districts(2022)
    assert not canton.get_regions(2022)
    assert not canton.get_superregions(2022)


def test_municipality_entities() -> None:
    # Municipality without quarters
    with freeze_time(f"{SUPPORTED_YEARS[-1]}-01-01"):
        principal = Municipality(
            name='Kriens', municipality='1059', canton='lu',
            canton_name='Kanton Luzern'
        )
        assert principal.entities == {
            year: {1059: {'name': 'Kriens'}} for year in SUPPORTED_YEARS
        }

    # Municipality with quarters
    principal = Municipality(
        name='Bern', municipality='351', canton='be', canton_name='Kanton Bern'
    )
    entities = {
        1: {'name': 'Innere Stadt'},
        2: {'name': 'Länggasse/Felsenau'},
        3: {'name': 'Mattenhof/Weissenbühl'},
        4: {'name': 'Kirchenfeld/Schosshalde'},
        5: {'name': 'Breitenrain/Lorraine'},
        6: {'name': 'Bümpliz/Bethlehem'},
    }
    assert principal.entities == {year: entities for year in SUPPORTED_YEARS}


def test_principal_years_available() -> None:
    principal: Canton | Municipality
    # Municipality without quarters/map
    with freeze_time(f"{SUPPORTED_YEARS[-1]}-01-01"):
        principal = Municipality(
            name='Kriens', municipality='1059', canton='lu',
            canton_name='Kanton Luzern'
        )
        assert not principal.is_year_available(2000)
        assert not principal.is_year_available(2000, map_required=False)
        for year in SUPPORTED_YEARS:
            assert not principal.is_year_available(year)
            assert principal.is_year_available(year, map_required=False)

    # Municipality with quarters/map
    principal = Municipality(
        name='Bern', municipality='351', canton='be', canton_name='Kanton Bern'
    )
    assert not principal.is_year_available(2000)
    assert not principal.is_year_available(2000, map_required=False)
    for year in SUPPORTED_YEARS_NO_MAP:
        assert not principal.is_year_available(year)
        assert principal.is_year_available(year, map_required=False)
    for year in SUPPORTED_YEARS_MAP:
        assert principal.is_year_available(year)
        assert principal.is_year_available(year, map_required=False)

    # Cantons
    for canton in Canton.CANTONS:
        principal = Canton(name=canton, canton=canton)

        if canton in {'bl', 'sg', 'zg'}:
            # Canton with additional map data
            for year in SUPPORTED_YEARS_NO_MAP_ADDITIONAL:
                assert not principal.is_year_available(year)
                assert principal.is_year_available(year, map_required=False)
            for year in SUPPORTED_YEARS_MAP_ADDITIONAL:
                assert principal.is_year_available(year)
                assert principal.is_year_available(year, map_required=False)
        else:
            # Canton with normal map data
            for year in SUPPORTED_YEARS_NO_MAP:
                assert not principal.is_year_available(year)
                assert principal.is_year_available(year, map_required=False)
            for year in SUPPORTED_YEARS_MAP:
                assert principal.is_year_available(year)
                assert principal.is_year_available(year, map_required=False)


def test_principal_label(election_day_app_zg: TestApp) -> None:
    principal: Canton | Municipality

    def translate(text: Any, locale: str) -> str:
        translator = election_day_app_zg.translations.get(locale)
        assert translator is not None
        return text.interpolate(translator.gettext(text))

    # Default (Canton)
    principal = Canton(name='sg', canton='sg')
    for label, locale, result in (
        ('entity', 'de_CH', 'Gemeinde'),
        ('entity', 'fr_CH', 'Commune'),
        ('entity', 'it_CH', 'Comune'),
        ('entity', 'rm_CH', 'Vischnanca'),
        ('entities', 'de_CH', 'Gemeinden'),
        ('entities', 'fr_CH', 'Communes'),
        ('entities', 'it_CH', 'Comuni'),
        ('entities', 'rm_CH', 'Vischnancas'),
        ('district', 'de_CH', 'Wahlkreis'),
        ('district', 'fr_CH', 'Circonscription électorale'),
        ('district', 'it_CH', 'Distretto elettorale'),
        ('district', 'rm_CH', 'Circul electoral'),
        ('districts', 'de_CH', 'Wahlkreise'),
        ('districts', 'fr_CH', 'Circonscriptions électorales'),
        ('districts', 'it_CH', 'Distretti elettorali'),
        ('districts', 'rm_CH', 'Circuls electorals'),
        ('region', 'de_CH', 'Wahlkreis'),
        ('region', 'fr_CH', 'Circonscription électorale'),
        ('region', 'it_CH', 'Distretto elettorale'),
        ('region', 'rm_CH', 'Circul electoral'),
        ('regions', 'de_CH', 'Wahlkreise'),
        ('regions', 'fr_CH', 'Circonscriptions électorales'),
        ('regions', 'it_CH', 'Distretti elettorali'),
        ('regions', 'rm_CH', 'Circuls electorals'),
        ('superregion', 'de_CH', 'Wahlkreis'),
        ('superregion', 'fr_CH', 'Circonscription électorale'),
        ('superregion', 'it_CH', 'Distretto elettorale'),
        ('superregion', 'rm_CH', 'Circul electoral'),
        ('superregions', 'de_CH', 'Wahlkreise'),
        ('superregions', 'fr_CH', 'Circonscriptions électorales'),
        ('superregions', 'it_CH', 'Distretti elettorali'),
        ('superregions', 'rm_CH', 'Circuls electorals'),
        ('mandates', 'de_CH', 'Mandate'),
        ('mandates', 'fr_CH', 'Mandats'),
        ('mandates', 'it_CH', 'Mandati'),
        ('mandates', 'rm_CH', 'Mandats'),
    ):
        assert translate(principal.label(label), locale) == result

    # BL
    principal = Canton(name='bl', canton='bl')
    for label, locale, result in (
        ('entity', 'de_CH', 'Gemeinde'),
        ('entity', 'fr_CH', 'Commune'),
        ('entity', 'it_CH', 'Comune'),
        ('entity', 'rm_CH', 'Vischnanca'),
        ('entities', 'de_CH', 'Gemeinden'),
        ('entities', 'fr_CH', 'Communes'),
        ('entities', 'it_CH', 'Comuni'),
        ('entities', 'rm_CH', 'Vischnancas'),
        ('district', 'de_CH', 'Bezirk'),
        ('district', 'fr_CH', 'District électoral'),
        ('district', 'it_CH', 'Distretto elettorale'),
        ('district', 'rm_CH', 'Circul electoral'),
        ('districts', 'de_CH', 'Bezirke'),
        ('districts', 'fr_CH', 'Districts électorales'),
        ('districts', 'it_CH', 'Distretti elettorali'),
        ('districts', 'rm_CH', 'Circuls electorals'),
        ('region', 'de_CH', 'Wahlkreis'),
        ('region', 'fr_CH', 'Circonscription électorale'),
        ('region', 'it_CH', 'Distretto elettorale'),
        ('region', 'rm_CH', 'Circul electoral'),
        ('regions', 'de_CH', 'Wahlkreise'),
        ('regions', 'fr_CH', 'Circonscriptions électorales'),
        ('regions', 'it_CH', 'Distretti elettorali'),
        ('regions', 'rm_CH', 'Circuls electorals'),
        ('superregion', 'de_CH', 'Region'),
        ('superregion', 'fr_CH', 'Région'),
        ('superregion', 'it_CH', 'Regione'),
        ('superregion', 'rm_CH', 'Regiun'),
        ('superregions', 'de_CH', 'Regionen'),
        ('superregions', 'fr_CH', 'Régions'),
        ('superregions', 'it_CH', 'Regioni'),
        ('superregions', 'rm_CH', 'Regiuns'),
        ('mandates', 'de_CH', 'Mandate'),
        ('mandates', 'fr_CH', 'Mandats'),
        ('mandates', 'it_CH', 'Mandati'),
        ('mandates', 'rm_CH', 'Mandats'),
    ):
        assert translate(principal.label(label), locale) == result

    # GR
    principal = Canton(name='gr', canton='gr')
    for label, locale, result in (
        ('entity', 'de_CH', 'Gemeinde'),
        ('entity', 'fr_CH', 'Commune'),
        ('entity', 'it_CH', 'Comune'),
        ('entity', 'rm_CH', 'Vischnanca'),
        ('entities', 'de_CH', 'Gemeinden'),
        ('entities', 'fr_CH', 'Communes'),
        ('entities', 'it_CH', 'Comuni'),
        ('entities', 'rm_CH', 'Vischnancas'),
        ('district', 'de_CH', 'Region'),
        ('district', 'fr_CH', 'Région'),
        ('district', 'it_CH', 'Regione'),
        ('district', 'rm_CH', 'Regiun'),
        ('districts', 'de_CH', 'Regionen'),
        ('districts', 'fr_CH', 'Régions'),
        ('districts', 'it_CH', 'Regioni'),
        ('districts', 'rm_CH', 'Regiuns'),
        ('region', 'de_CH', 'Wahlkreis'),
        ('region', 'fr_CH', 'Circonscription électorale'),
        ('region', 'it_CH', 'Circondario elettorale'),
        ('region', 'rm_CH', 'Circul electoral'),
        ('regions', 'de_CH', 'Wahlkreise'),
        ('regions', 'fr_CH', 'Circonscriptions électorales'),
        ('regions', 'it_CH', 'Circondari elettorali'),
        ('regions', 'rm_CH', 'Circuls electorals'),
        ('superregion', 'de_CH', 'Wahlkreis'),
        ('superregion', 'fr_CH', 'Circonscription électorale'),
        ('superregion', 'it_CH', 'Distretto elettorale'),
        ('superregion', 'rm_CH', 'Circul electoral'),
        ('superregions', 'de_CH', 'Wahlkreise'),
        ('superregions', 'fr_CH', 'Circonscriptions électorales'),
        ('superregions', 'it_CH', 'Distretti elettorali'),
        ('superregions', 'rm_CH', 'Circuls electorals'),
        ('mandates', 'de_CH', 'Sitze'),
        ('mandates', 'fr_CH', 'Sièges'),
        ('mandates', 'it_CH', 'Seggi'),
        ('mandates', 'rm_CH', 'Sezs'),
    ):
        assert translate(principal.label(label), locale) == result

    # SZ
    principal = Canton(name='sz', canton='sz')
    for label, locale, result in (
        ('entity', 'de_CH', 'Gemeinde'),
        ('entity', 'fr_CH', 'Commune'),
        ('entity', 'it_CH', 'Comune'),
        ('entity', 'rm_CH', 'Vischnanca'),
        ('entities', 'de_CH', 'Gemeinden'),
        ('entities', 'fr_CH', 'Communes'),
        ('entities', 'it_CH', 'Comuni'),
        ('entities', 'rm_CH', 'Vischnancas'),
        ('district', 'de_CH', 'Bezirk'),
        ('district', 'fr_CH', 'District électoral'),
        ('district', 'it_CH', 'Distretto elettorale'),
        ('district', 'rm_CH', 'Circul electoral'),
        ('districts', 'de_CH', 'Bezirke'),
        ('districts', 'fr_CH', 'Districts électorales'),
        ('districts', 'it_CH', 'Distretti elettorali'),
        ('districts', 'rm_CH', 'Circuls electorals'),
        ('region', 'de_CH', 'Wahlkreis'),
        ('region', 'fr_CH', 'Circonscription électorale'),
        ('region', 'it_CH', 'Distretto elettorale'),
        ('region', 'rm_CH', 'Circul electoral'),
        ('regions', 'de_CH', 'Wahlkreise'),
        ('regions', 'fr_CH', 'Circonscriptions électorales'),
        ('regions', 'it_CH', 'Distretti elettorali'),
        ('regions', 'rm_CH', 'Circuls electorals'),
        ('superregion', 'de_CH', 'Wahlkreis'),
        ('superregion', 'fr_CH', 'Circonscription électorale'),
        ('superregion', 'it_CH', 'Distretto elettorale'),
        ('superregion', 'rm_CH', 'Circul electoral'),
        ('superregions', 'de_CH', 'Wahlkreise'),
        ('superregions', 'fr_CH', 'Circonscriptions électorales'),
        ('superregions', 'it_CH', 'Distretti elettorali'),
        ('superregions', 'rm_CH', 'Circuls electorals'),
        ('mandates', 'de_CH', 'Mandate'),
        ('mandates', 'fr_CH', 'Mandats'),
        ('mandates', 'it_CH', 'Mandati'),
        ('mandates', 'rm_CH', 'Mandats'),
    ):
        assert translate(principal.label(label), locale) == result

    # ZG
    principal = Canton(name='sz', canton='sz')
    for label, locale, result in (
        ('entity', 'de_CH', 'Gemeinde'),
        ('entity', 'fr_CH', 'Commune'),
        ('entity', 'it_CH', 'Comune'),
        ('entity', 'rm_CH', 'Vischnanca'),
        ('entities', 'de_CH', 'Gemeinden'),
        ('entities', 'fr_CH', 'Communes'),
        ('entities', 'it_CH', 'Comuni'),
        ('entities', 'rm_CH', 'Vischnancas'),
        ('district', 'de_CH', 'Bezirk'),
        ('district', 'fr_CH', 'District électoral'),
        ('district', 'it_CH', 'Distretto elettorale'),
        ('district', 'rm_CH', 'Circul electoral'),
        ('districts', 'de_CH', 'Bezirke'),
        ('districts', 'fr_CH', 'Districts électorales'),
        ('districts', 'it_CH', 'Distretti elettorali'),
        ('districts', 'rm_CH', 'Circuls electorals'),
        ('region', 'de_CH', 'Wahlkreis'),
        ('region', 'fr_CH', 'Circonscription électorale'),
        ('region', 'it_CH', 'Distretto elettorale'),
        ('region', 'rm_CH', 'Circul electoral'),
        ('regions', 'de_CH', 'Wahlkreise'),
        ('regions', 'fr_CH', 'Circonscriptions électorales'),
        ('regions', 'it_CH', 'Distretti elettorali'),
        ('regions', 'rm_CH', 'Circuls electorals'),
        ('superregion', 'de_CH', 'Wahlkreis'),
        ('superregion', 'fr_CH', 'Circonscription électorale'),
        ('superregion', 'it_CH', 'Distretto elettorale'),
        ('superregion', 'rm_CH', 'Circul electoral'),
        ('superregions', 'de_CH', 'Wahlkreise'),
        ('superregions', 'fr_CH', 'Circonscriptions électorales'),
        ('superregions', 'it_CH', 'Distretti elettorali'),
        ('superregions', 'rm_CH', 'Circuls electorals'),
        ('mandates', 'de_CH', 'Mandate'),
        ('mandates', 'fr_CH', 'Mandats'),
        ('mandates', 'it_CH', 'Mandati'),
        ('mandates', 'rm_CH', 'Mandats'),
    ):
        assert translate(principal.label(label), locale) == result

    # Bern
    principal = Municipality(
        name='Bern', municipality='351', canton='be', canton_name='Kanton Bern'
    )
    for label, locale, result in (
        ('entity', 'de_CH', 'Stadtteil'),
        ('entities', 'de_CH', 'Stadtteile')
    ):
        assert translate(principal.label(label), locale) == result
