from __future__ import annotations

from onegov.landsgemeinde.forms import AgendaItemForm
from onegov.landsgemeinde.forms import AssemblyForm
from onegov.landsgemeinde.forms import VotumForm
from unittest.mock import Mock


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.landsgemeinde.models import Assembly
    from sqlalchemy.orm import Session
    from webob.multidict import MultiDict

    DummyPostDataBase = MultiDict[str, Any]
else:
    DummyPostDataBase = dict


class DummyPostData(DummyPostDataBase):
    def getlist(self, key: str) -> list[Any]:
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def test_assembly_form(session: Session, assembly: Assembly) -> None:
    session.add(assembly)
    session.flush()
    session.expire_all()

    # validate: no data
    form = AssemblyForm()
    form.request = Mock()
    form.request.session = session
    form.model = assembly
    assert not form.validate()
    assert form.errors == {
        'date': ['This field is required.'],
        'state': ['This field is required.']
    }

    # validate: date already used
    form = AssemblyForm(
        DummyPostData({'date': '2023-05-07', 'state': 'ongoing'})
    )
    form.request = Mock()
    form.request.session = session
    form.model = None
    assert not form.validate()
    assert form.errors == {'date': ['Date already used.']}

    # validate: new date
    form = AssemblyForm(
        DummyPostData({'date': '2022-05-01', 'state': 'ongoing'})
    )
    form.request = Mock()
    form.request.session = session
    form.model = assembly
    assert form.validate()

    # validate: same date on existing
    form = AssemblyForm(
        DummyPostData({'date': '2023-05-07', 'state': 'ongoing'})
    )
    form.request = Mock()
    form.request.session = session
    form.model = assembly
    assert form.validate()


def test_agenda_item_form(session: Session, assembly: Assembly) -> None:
    session.add(assembly)
    session.flush()
    session.expire_all()

    # next number
    form = AgendaItemForm()
    form.request = Mock()
    form.request.session = session
    form.model = assembly.agenda_items[0]
    assert form.next_number == 3

    # useful data
    assert form.get_useful_data()['assembly_id'] == assembly.id

    # validate: no data
    form = AgendaItemForm()
    form.request = Mock()
    form.request.session = session
    form.model = assembly.agenda_items[0]
    assert not form.validate()
    assert form.errors == {'state': ['This field is required.']}

    # validate: number already used
    form = AgendaItemForm(DummyPostData({'number': '1', 'state': 'ongoing'}))
    form.request = Mock()
    form.request.session = session
    form.model = Mock()
    form.model.assembly = assembly
    assert not form.validate()
    assert form.errors == {'number': ['Number already used.']}

    # validate: new number
    form = AgendaItemForm(DummyPostData({'number': '4', 'state': 'ongoing'}))
    form.request = Mock()
    form.request.session = session
    form.model = assembly.agenda_items[0]
    assert form.validate()

    # validate: same number on existing
    form = AgendaItemForm(DummyPostData({'number': '1', 'state': 'ongoing'}))
    form.request = Mock()
    form.request.session = session
    form.model = assembly.agenda_items[0]
    assert form.validate()

    # validate: invalid video timestamp
    form = AgendaItemForm(
        DummyPostData({'video_timestamp': 'foo', 'state': 'ongoing'})
    )
    form.request = Mock()
    form.request.session = session
    form.model = assembly.agenda_items[0]
    assert not form.validate()
    assert form.errors == {'video_timestamp': ['Invalid timestamp.']}

    # validate: valid video timestamp
    form = AgendaItemForm(
        DummyPostData({'video_timestamp': '1m', 'state': 'ongoing'})
    )
    form.request = Mock()
    form.request.session = session
    form.model = assembly.agenda_items[0]
    assert form.validate()


def test_votum_form(session: Session, assembly: Assembly) -> None:
    session.add(assembly)
    session.flush()
    session.expire_all()

    # next number
    form = VotumForm()
    form.request = Mock()
    form.request.session = session
    form.model = assembly.agenda_items[0].vota[0]
    assert form.next_number == 3

    # useful data
    assert form.get_useful_data()['agenda_item_id'] == (
        assembly.agenda_items[0].id)

    # validate: no data
    form = VotumForm()
    form.request = Mock()
    form.request.session = session
    form.model = assembly.agenda_items[0].vota[0]
    assert not form.validate()
    assert form.errors == {'state': ['This field is required.']}

    # validate: number already used
    form = VotumForm(DummyPostData({'number': '1', 'state': 'ongoing'}))
    form.request = Mock()
    form.request.session = session
    form.model = Mock()
    form.model.agenda_item = assembly.agenda_items[0]
    assert not form.validate()
    assert form.errors == {'number': ['Number already used.']}

    # validate: new number
    form = VotumForm(DummyPostData({'number': '4', 'state': 'ongoing'}))
    form.request = Mock()
    form.request.session = session
    form.model = assembly.agenda_items[0].vota[0]
    assert form.validate()

    # validate: same number on existing
    form = VotumForm(DummyPostData({'number': '1', 'state': 'ongoing'}))
    form.request = Mock()
    form.request.session = session
    form.model = assembly.agenda_items[0].vota[0]
    assert form.validate()

    # validate: invalid video timestamp
    form = VotumForm(
        DummyPostData({'video_timestamp': 'foo', 'state': 'ongoing'})
    )
    form.request = Mock()
    form.request.session = session
    form.model = Mock()
    form.model.agenda_item = assembly.agenda_items[0]
    assert not form.validate()
    assert form.errors == {'video_timestamp': ['Invalid timestamp.']}

    # validate: valid video timestamp
    form = VotumForm(
        DummyPostData({'video_timestamp': '1m', 'state': 'ongoing'})
    )
    form.request = Mock()
    form.request.session = session
    form.model = Mock()
    form.model.agenda_item = assembly.agenda_items[0]
    assert form.validate()
