from datetime import date
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import Vote
from onegov.election_day.forms import ChangeIdForm
from tests.onegov.election_day.common import DummyPostData
from tests.onegov.election_day.common import DummyRequest


def test_change_id_form(session):
    models = {
        'vote': Vote(
            title='Vote',
            domain='federation',
            date=date(2015, 6, 14)
        ),
        'election': Election(
            title='Election',
            domain='federation',
            date=date(2015, 6, 14)
        ),
        'compound': ElectionCompound(
            title='Compound',
            domain='canton',
            date=date(2015, 6, 14),
        )
    }

    for name, model in models.items():
        session.add(model)
        session.add(model.__class__(
            id=f'{name}-copy',
            title=model.title,
            domain=model.domain,
            date=model.date
        ))
        session.flush()

        form = ChangeIdForm()
        form.apply_model(model)
        assert form.id.data == name
        assert not form.validate()
        assert form.errors == {'id': ['This field is required.']}

        form = ChangeIdForm(DummyPostData({'id': f'{name} {name}'}))
        form.request = DummyRequest(session=session)
        form.model = model
        assert not form.validate()
        assert form.errors == {'id': ['Invalid ID']}

        form = ChangeIdForm(DummyPostData({'id': f'{name}-copy'}))
        form.request = DummyRequest(session=session)
        form.model = model
        assert not form.validate()
        assert form.errors == {'id': ['ID already exists']}

        form = ChangeIdForm(DummyPostData({'id': f'{name}-new'}))
        form.request = DummyRequest(session=session)
        form.model = model
        assert form.validate()
        form.update_model(model)
        session.flush()
        assert session.query(model.__class__).filter_by(id=f'{name}-new').one()
