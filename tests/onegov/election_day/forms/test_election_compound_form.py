from datetime import date
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import ProporzElection
from onegov.election_day.forms import ElectionCompoundForm
from onegov.election_day.models import Canton
from tests.onegov.election_day.common import DummyPostData
from tests.onegov.election_day.common import DummyRequest
from wtforms.validators import InputRequired


def test_election_compound_form_on_request(session):
    session.add(
        ProporzElection(
            title='r1',
            domain='region',
            shortcode='2',
            date=date(2001, 1, 1))
    )
    session.add(
        ProporzElection(
            title='d1',
            domain='district',
            shortcode='1',
            date=date(2001, 1, 1))
    )
    session.add(
        ProporzElection(
            title='m1',
            domain='municipality',
            date=date(2000, 1, 1))
    )
    session.add(
        Election(
            title='m2',
            domain='municipality',
            date=date(2000, 1, 1))
    )
    session.add(
        ProporzElection(
            title='f1',
            domain='federation',
            date=date(2001, 1, 1))
    )
    session.flush()

    form = ElectionCompoundForm()
    form.request = DummyRequest(session=session)
    form.request.default_locale = 'de_CH'
    form.request.app.principal = Canton(name='zg', canton='zg')
    form.on_request()
    assert [x[0] for x in form.domain_elections.choices] == ['municipality']
    assert [x[0] for x in form.region_elections.choices] == ['r1']
    assert [x[0] for x in form.district_elections.choices] == ['d1']
    assert [x[0] for x in form.municipality_elections.choices] == ['m1']
    assert isinstance(form.election_de.validators[0], InputRequired)
    assert form.election_fr.validators == []
    assert form.election_it.validators == []
    assert form.election_rm.validators == []

    form = ElectionCompoundForm()
    form.request = DummyRequest(session=session)
    form.request.default_locale = 'fr_CH'
    form.request.app.principal = Canton(name='gr', canton='gr')
    form.on_request()
    assert [x[0] for x in form.domain_elections.choices] == [
        'region', 'district', 'municipality'
    ]
    assert [x[0] for x in form.region_elections.choices] == ['r1']
    assert [x[0] for x in form.district_elections.choices] == ['d1']
    assert [x[0] for x in form.municipality_elections.choices] == ['m1']
    assert form.election_de.validators == []
    assert isinstance(form.election_fr.validators[0], InputRequired)
    assert form.election_it.validators == []
    assert form.election_rm.validators == []


def test_election_compound_form_validate(session):
    session.add(
        ProporzElection(
            title='election-1',
            domain='region',
            date=date(2001, 1, 1))
    )
    session.add(
        ProporzElection(
            title='election-2',
            domain='region',
            date=date(2001, 1, 1))
    )
    session.flush()

    form = ElectionCompoundForm()
    form.request = DummyRequest(session=session)
    form.request.app.principal = Canton(name='gr', canton='gr')
    form.on_request()

    form.process(DummyPostData({
        'election_de': 'Elections',
        'domain': 'canton',
        'domain_elections': 'region',
        'date': '2012-01-01',
        'region_elections': ['election-1'],
    }))
    assert form.validate()

    form.process(DummyPostData({
        'election_de': 'Elections',
        'domain': 'canton',
        'domain_elections': 'region',
        'date': '2012-01-01',
        'region_elections': ['election-1', 'election-2'],
    }))
    assert form.validate()


def test_election_compound_form_model(session, related_link_labels):
    date_ = date(2001, 1, 1)
    e_r = Election(domain='region', title='e', id='e-r', date=date_)
    e_d = Election(domain='district', title='e', id='e-d', date=date_)
    e_m = Election(domain='municipality', title='e', id='e-m', date=date_)
    session.add(e_r)
    session.add(e_d)
    session.add(e_m)
    session.flush()

    model = ElectionCompound()
    model.title = 'Elections (DE)'
    model.title_translations['de_CH'] = 'Elections (DE)'
    model.title_translations['fr_CH'] = 'Elections (FR)'
    model.title_translations['it_CH'] = 'Elections (IT)'
    model.title_translations['rm_CH'] = 'Elections (RM)'
    model.date = date(2012, 1, 1)
    model.domain = 'canton'
    model.domain_elections = 'region'
    model.shortcode = 'xy'
    model.related_link = 'http://u.rl'
    model.related_link_label = related_link_labels
    model.show_list_groups = True
    model.show_lists = True
    model.show_party_strengths = True
    model.show_party_panachage = True
    model.elections = [e_r]
    model.pukelsheim = True
    model.completes_manually = True
    model.manually_completed = True
    model.colors = {
        'FDP': '#3a8bc1',
        'CVP': '#ff9100',
    }
    session.add(model)

    form = ElectionCompoundForm()
    form.apply_model(model)
    assert form.election_de.data == 'Elections (DE)'
    assert form.election_fr.data == 'Elections (FR)'
    assert form.election_it.data == 'Elections (IT)'
    assert form.election_rm.data == 'Elections (RM)'
    assert form.date.data == date(2012, 1, 1)
    assert form.domain.data == 'canton'
    assert form.domain_elections.data == 'region'
    assert form.shortcode.data == 'xy'
    assert form.related_link.data == 'http://u.rl'
    assert form.related_link_label_de.data == 'DE'
    assert form.related_link_label_fr.data == 'FR'
    assert form.related_link_label_it.data == 'IT'
    assert form.related_link_label_rm.data == 'RM'
    assert form.show_list_groups.data is True
    assert form.show_lists.data is True
    assert form.show_party_strengths.data is True
    assert form.show_party_panachage.data is True
    assert form.region_elections.data == ['e-r']
    assert form.district_elections.data == []
    assert form.municipality_elections.data == []
    assert form.pukelsheim.data is True
    assert form.completes_manually.data is True
    assert form.manually_completed.data is True
    assert form.colors.data == (
        'CVP #ff9100\n'
        'FDP #3a8bc1'
    )

    form.election_de.data = 'Some Elections (DE)'
    form.election_fr.data = 'Some Elections (FR)'
    form.election_it.data = 'Some Elections (IT)'
    form.election_rm.data = 'Some Elections (RM)'
    form.date.data = date(2016, 1, 1)
    form.domain.data = 'canton'
    form.domain_elections.data = 'district'
    form.shortcode.data = 'yz'
    form.related_link.data = 'http://ur.l'
    form.show_list_groups.data = False
    form.show_lists.data = False
    form.show_party_strengths.data = False
    form.show_party_panachage.data = False
    form.region_elections.data = ['e-r']
    form.district_elections.data = ['e-d']
    form.municipality_elections.data = ['e-m']
    form.pukelsheim.data = False
    form.completes_manually.data = False
    form.manually_completed.data = False
    form.colors.data = (
        'CVP #ff9100\r\n'
        'SP Juso #dd0e0e\n'
        'FDP   #3a8bc1\n'
        'GLP\t\t#aeca00\n'
    )

    form.request = DummyRequest(session=session)
    form.request.app.principal = Canton(name='gr', canton='gr')
    form.on_request()
    form.update_model(model)
    assert model.title == 'Some Elections (DE)'
    assert model.title_translations['de_CH'] == 'Some Elections (DE)'
    assert model.title_translations['fr_CH'] == 'Some Elections (FR)'
    assert model.title_translations['it_CH'] == 'Some Elections (IT)'
    assert model.title_translations['rm_CH'] == 'Some Elections (RM)'
    assert model.date == date(2016, 1, 1)
    assert model.domain == 'canton'
    assert model.domain_elections == 'district'
    assert model.shortcode == 'yz'
    assert model.related_link == 'http://ur.l'
    assert model.pukelsheim is False
    assert model.completes_manually is False
    assert model.manually_completed is False
    assert form.show_list_groups.data is False
    assert form.show_lists.data is False
    assert form.show_party_strengths.data is False
    assert form.show_party_panachage.data is False
    assert sorted([e.id for e in model.elections]) == ['e-d']
    assert model.colors == {
        'CVP': '#ff9100',
        'FDP': '#3a8bc1',
        'GLP': '#aeca00',
        'SP Juso': '#dd0e0e',
    }

    form.domain_elections.data = 'municipality'
    form.update_model(model)
    assert sorted([e.id for e in model.elections]) == ['e-m']
