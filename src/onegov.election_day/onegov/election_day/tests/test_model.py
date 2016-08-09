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
        name: Foobar
        logo:
        canton: zg
        color: '#000'
    """))

    assert principal.name == 'Foobar'
    assert principal.name == 'Foobar'
    assert principal.logo is None
    assert principal.canton == 'zg'
    assert principal.color == '#000'
    assert principal.base is None
    assert principal.base_domain is None
    assert principal.analytics is None

    principal = Principal.from_yaml(textwrap.dedent("""
        name: Foobar
        logo:
        canton: zg
        color: '#000'
        base: 'http://www.zg.ch'
        analytics: "<script type=\\"text/javascript\\"></script>"
    """))

    assert principal.name == 'Foobar'
    assert principal.logo is None
    assert principal.canton == 'zg'
    assert principal.color == '#000'
    assert principal.base == 'http://www.zg.ch'
    assert principal.base_domain == 'zg.ch'
    assert principal.analytics == '<script type="text/javascript"></script>'


def test_municipalities():
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

    for year in range(2009, 2013):
        assert not principal.is_year_available(year)
    for year in range(2013, 2017):
        assert principal.is_year_available(year)
    for year in range(2009, 2017):
        assert principal.is_year_available(year, map_required=False)

    for canton in cantons:
        principal = Principal(
            name=canton, canton=canton, logo=None, color=None
        )

        assert principal.municipalities[2009]
        assert principal.municipalities[2010]
        assert principal.municipalities[2011]
        assert principal.municipalities[2012]
        assert principal.municipalities[2013]
        assert principal.municipalities[2014]
        assert principal.municipalities[2015]


def test_archive(session):
    request = DummyRequest()
    archive = Archive(session)

    def _json(items):
        return archive.latest_to_list(items, request)

    assert archive.for_date(2015).date == 2015

    assert archive.get_years() == []
    assert archive.latest() is None

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

    assert archive.latest() == archive.for_date(2016).by_date()
    assert archive.latest() == archive.for_date('2016').by_date()
    assert archive.latest() == archive.for_date('2016-01-01').by_date()

    latest_json = _json(archive.latest(group=False))
    assert latest_json == _json(archive.for_date(2016).by_date(group=False))
    assert latest_json == _json(archive.for_date('2016').by_date(group=False))
    assert latest_json == _json(
        archive.for_date('2016-01-01').by_date(group=False)
    )

    assert archive.for_date('2016-02-02').by_date() is None
    assert _json(archive.for_date('2016-02-02').by_date(group=False)) == []

    for year in (2009, 2011, 2014, 2016):
        assert (
            ('election', 'federation', date(year, 1, 1)),
            [session.query(Election).filter_by(date=date(year, 1, 1)).one()]
        ) in archive.for_date(year).by_date()

        assert {
            'data_url': 'Election/json',
            'domain': 'federation',
            'url': 'Election',
            'title': {'de_CH': 'Election {}'.format(year)},
            'type': 'election',
            'date': '{}-01-01'.format(year),
            'progress': {'total': 0, 'counted': 0}
        } in _json(archive.for_date(year).by_date(group=False))

    for year in (2007, 2011, 2015, 2016):
        assert (
            ('vote', 'federation', date(year, 1, 1)),
            [session.query(Vote).filter_by(date=date(year, 1, 1)).one()]
        ) in archive.for_date(year).by_date()

        assert {
            'answer': '',
            'data_url': 'Vote/json',
            'date': '{}-01-01'.format(year),
            'domain': 'federation',
            'nays_percentage': 100.0,
            'progress': {'counted': 0.0, 'total': 0.0},
            'title': {'de_CH': 'Vote {}'.format(year)},
            'type': 'vote',
            'url': 'Vote',
            'yeas_percentage': 0.0
        } in _json(archive.for_date(year).by_date(group=False))
