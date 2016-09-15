import textwrap

from datetime import date
from onegov.ballot import Election, Vote
from onegov.election_day.models import Archive, Principal
from onegov.election_day.models.principal import cantons


class DummyRequest(object):

    def link(self, model, name=''):
        return '{}/{}'.format(model.__class__.__name__, name).rstrip('/')


def test_load_principal():
    principal = Principal.from_yaml(textwrap.dedent("""
        name: Kanton Zug
        logo:
        canton: zg
        color: '#000'
    """))

    assert principal.name == 'Kanton Zug'
    assert principal.logo is None
    assert principal.canton == 'zg'
    assert principal.municipality is None
    assert principal.color == '#000'
    assert principal.base is None
    assert principal.base_domain is None
    assert principal.analytics is None
    assert principal.use_maps is True
    assert principal.domain is 'canton'
    assert list(principal.available_domains.keys()) == ['federation', 'canton']

    principal = Principal.from_yaml(textwrap.dedent("""
        name: Kanton Zug
        logo:
        canton: zg
        color: '#000'
        base: 'http://www.zg.ch'
        analytics: "<script type=\\"text/javascript\\"></script>"
        use_maps: false
    """))

    assert principal.name == 'Kanton Zug'
    assert principal.logo is None
    assert principal.canton == 'zg'
    assert principal.municipality is None
    assert principal.color == '#000'
    assert principal.base == 'http://www.zg.ch'
    assert principal.base_domain == 'zg.ch'
    assert principal.analytics == '<script type="text/javascript"></script>'
    assert principal.use_maps is True
    assert principal.domain is 'canton'
    assert list(principal.available_domains.keys()) == ['federation', 'canton']

    principal = Principal.from_yaml(textwrap.dedent("""
        name: Stadt Bern
        logo:
        municipality: '351'
        color: '#000'
    """))

    assert principal.name == 'Stadt Bern'
    assert principal.logo is None
    assert principal.canton is None
    assert principal.municipality == '351'
    assert principal.color == '#000'
    assert principal.base is None
    assert principal.base_domain is None
    assert principal.analytics is None
    assert principal.use_maps is False
    assert principal.domain is 'municipality'
    assert list(principal.available_domains.keys()) == [
        'federation', 'canton', 'municipality'
    ]

    principal = Principal.from_yaml(textwrap.dedent("""
        name: Stadt Bern
        logo:
        municipality: '351'
        color: '#000'
        use_maps: true
    """))

    assert principal.name == 'Stadt Bern'
    assert principal.logo is None
    assert principal.canton is None
    assert principal.municipality == '351'
    assert principal.color == '#000'
    assert principal.base is None
    assert principal.base_domain is None
    assert principal.analytics is None
    assert principal.use_maps is True
    assert principal.domain is 'municipality'
    assert list(principal.available_domains.keys()) == [
        'federation', 'canton', 'municipality'
    ]


def test_municipalities():
    principal = Principal(
        name='Bern', municipality='351', logo=None, color=None
    )
    assert principal.municipalities == {}

    principal = Principal(name='Zug', canton='zg', logo=None, color=None)

    municipalities = {
        1701: {'name': 'Baar'},
        1702: {'name': 'Cham'},
        1703: {'name': 'Hünenberg'},
        1704: {'name': 'Menzingen'},
        1705: {'name': 'Neuheim'},
        1706: {'name': 'Oberägeri'},
        1707: {'name': 'Risch'},
        1708: {'name': 'Steinhausen'},
        1709: {'name': 'Unterägeri'},
        1710: {'name': 'Walchwil'},
        1711: {'name': 'Zug'},
    }

    assert principal.municipalities == {
        2009: municipalities,
        2010: municipalities,
        2011: municipalities,
        2012: municipalities,
        2013: municipalities,
        2014: municipalities,
        2015: municipalities,
        2016: municipalities,
    }

    for canton in cantons:
        principal = Principal(
            name=canton, canton=canton, logo=None, color=None
        )

        for year in range(2009, 2017):
            assert principal.municipalities[year]


def test_districts():
    principal = Principal(name='Zug', canton='zg', logo=None, color=None)
    assert principal.districts == {}

    principal = Principal(
        name='Kriens', municipality='1059', logo=None, color=None
    )

    assert principal.districts == {
        2009: {1059: {'name': 'Kriens'}},
        2010: {1059: {'name': 'Kriens'}},
        2011: {1059: {'name': 'Kriens'}},
        2012: {1059: {'name': 'Kriens'}},
        2013: {1059: {'name': 'Kriens'}},
        2014: {1059: {'name': 'Kriens'}},
        2015: {1059: {'name': 'Kriens'}},
        2016: {1059: {'name': 'Kriens'}},
    }

    principal = Principal(
        name='Bern', municipality='351', logo=None, color=None
    )
    districts = {
        1: {'name': 'Innere Stadt'},
        2: {'name': 'Länggasse/Felsenau'},
        3: {'name': 'Mattenhof/Weissenbühl'},
        4: {'name': 'Kirchenfeld/Schosshalde'},
        5: {'name': 'Breitenrain/Lorraine'},
        6: {'name': 'Bümpliz/Bethlehem'},
    }
    assert principal.districts == {
        2012: districts,
        2013: districts,
        2014: districts,
        2015: districts,
        2016: districts
    }


def test_entities():
    principal = Principal(name='Zug', canton='zg', logo=None, color=None)
    assert principal.entities == principal.municipalities

    principal = Principal(
        name='Kriens', municipality='1059', logo=None, color=None
    )
    assert principal.entities == principal.districts

    principal = Principal(
        name='Bern', municipality='351', logo=None, color=None
    )
    assert principal.entities == principal.districts


def test_years_available():
    principal = Principal(
        name='Kriens', municipality='1059', logo=None, color=None
    )
    assert not principal.is_year_available(2000)
    assert not principal.is_year_available(2016)
    assert not principal.is_year_available(2000, map_required=False)
    assert principal.is_year_available(2016, map_required=False)

    principal = Principal(
        name='Bern', municipality='351', logo=None, color=None
    )
    assert not principal.is_year_available(2000)
    assert principal.is_year_available(2016)
    assert not principal.is_year_available(2000, map_required=False)
    assert principal.is_year_available(2016, map_required=False)

    for canton in cantons:
        principal = Principal(
            name=canton, canton=canton, logo=None, color=None
        )

        for year in range(2009, 2013):
            assert not principal.is_year_available(year)
        for year in range(2013, 2017):
            assert principal.is_year_available(year)
        for year in range(2009, 2017):
            assert principal.is_year_available(year, map_required=False)


def test_archive(session):
    archive = Archive(session)

    assert archive.for_date(2015).date == 2015

    assert archive.get_years() == []
    assert archive.latest() == []
    assert archive.for_date(2015).by_date() == []

    for year in (2009, 2011, 2014, 2016):
        session.add(
            Election(
                title="Election {}".format(year),
                domain='federation',
                type='majorz',
                date=date(year, 1, 1),
            )
        )
    for year in (2007, 2011, 2015, 2016):
        session.add(
            Vote(
                title="Vote {}".format(year),
                domain='federation',
                date=date(year, 1, 1),
            )
        )

    session.flush()

    assert archive.get_years() == [2016, 2015, 2014, 2011, 2009, 2007]

    for date_ in (2016, '2016', '2016-01-01'):
        assert archive.latest() == archive.for_date(date_).by_date()

    assert archive.for_date('2016-02-02').by_date() == []

    for year in (2009, 2011, 2014, 2016):
        item = session.query(Election).filter_by(date=date(year, 1, 1)).one()
        items = archive.for_date(year).by_date()
        assert item in items

        groups = archive.group_items(items)
        assert groups[date(year, 1, 1)]['federation']['election'] == [item]

    for year in (2007, 2011, 2015, 2016):
        item = session.query(Vote).filter_by(date=date(year, 1, 1)).one()
        items = archive.for_date(year).by_date()
        assert item in items

        groups = archive.group_items(items)
        assert groups[date(year, 1, 1)]['federation']['vote'] == [item]
