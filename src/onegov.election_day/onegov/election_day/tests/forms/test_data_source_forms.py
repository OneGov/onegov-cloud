from datetime import date
from onegov.ballot import Election
from onegov.ballot import Vote
from onegov.election_day.forms import DataSourceForm
from onegov.election_day.forms import DataSourceItemForm
from onegov.election_day.models import DataSource
from onegov.election_day.models import DataSourceItem
from onegov.election_day.tests import DummyPostData


def test_data_source_form():
    # Validation
    assert not DataSourceForm().validate()
    assert DataSourceForm(
        DummyPostData({'name': 'name', 'upload_type': 'vote'})
    ).validate()
    assert DataSourceForm(
        DummyPostData({'name': 'name', 'upload_type': 'majorz'})
    ).validate()
    assert DataSourceForm(
        DummyPostData({'name': 'name', 'upload_type': 'proporz'})
    ).validate()

    # Update model/form
    form = DataSourceForm()
    model = DataSource(type='vote', name='ds_vote')

    form.apply_model(model)
    assert form.upload_type.data == 'vote'
    assert form.name.data == 'ds_vote'

    form.upload_type.data = 'majorz'
    form.name.data = 'ds_majorz'
    form.update_model(model)
    assert model.type == 'majorz'
    assert model.name == 'ds_majorz'


def test_data_source_item_form():
    # Validation
    assert not DataSourceItemForm().validate()
    form = DataSourceItemForm(
        DummyPostData({'district': '1', 'number': '2', 'item': 'item'})
    )
    form.item.choices = [('item', 'Item')]
    assert form.validate()

    # Update model/form
    model = DataSourceItem(
        district='1', number='2', vote_id='vote-id', election_id='election-id'
    )

    form = DataSourceItemForm()
    form.type = 'vote'
    form.apply_model(model)
    assert form.district.data == '1'
    assert form.number.data == '2'
    assert form.item.data == 'vote-id'
    form.district.data = '11'
    form.number.data = '22'
    form.item.data = 'new-vote-id'
    form.update_model(model)
    assert model.district == '11'
    assert model.number == '22'
    assert model.vote_id == 'new-vote-id'

    form = DataSourceItemForm()
    form.type = 'majorz'
    form.apply_model(model)
    assert form.district.data == '11'
    assert form.number.data == '22'
    assert form.item.data == 'election-id'
    form.district.data = '111'
    form.number.data = '222'
    form.item.data = 'new-election-id'
    form.update_model(model)
    assert model.district == '111'
    assert model.number == '222'
    assert model.election_id == 'new-election-id'


def test_data_source_item_form_populate(session):
    form = DataSourceItemForm()

    session.add(DataSource(type='vote', name='dsv'))
    session.add(DataSource(type='majorz', name='dsm'))
    session.add(DataSource(type='proporz', name='dsp'))
    session.flush()

    dsv = session.query(DataSource).filter_by(type='vote').one()
    dsm = session.query(DataSource).filter_by(type='majorz').one()
    dsp = session.query(DataSource).filter_by(type='proporz').one()

    form.populate(dsv)
    assert form.callout == 'No votes yet.'
    assert not form.item.choices

    form.populate(dsm)
    assert form.callout == 'No elections yet.'
    assert not form.item.choices

    form.populate(dsp)
    assert form.callout == 'No elections yet.'
    assert not form.item.choices

    dt = date(2015, 6, 14)
    session.add(Vote(title='v', domain='canton', date=dt))
    session.add(Election(title='m', type='majorz', domain='canton', date=dt))
    session.add(Election(title='p', type='proporz', domain='canton', date=dt))

    form.populate(dsv)
    assert not form.callout
    assert form.item.choices == [('v', 'v')]

    form.populate(dsm)
    assert not form.callout
    assert form.item.choices == [('m', 'm')]

    form.populate(dsp)
    assert not form.callout
    assert form.item.choices == [('p', 'p')]
