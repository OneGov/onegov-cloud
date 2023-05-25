from datetime import date
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import Votum
from pytest import fixture


@fixture(scope='function')
def assembly():
    assembly = Assembly(state='scheduled', date=date(2023, 5, 7))
    agenda_item_1 = AgendaItem(state='scheduled', number=1)
    agenda_item_2 = AgendaItem(state='scheduled', number=2)
    votum_1_1 = Votum(state='scheduled', number=1)
    votum_1_2 = Votum(state='scheduled', number=2)
    votum_2_1 = Votum(state='scheduled', number=1)
    votum_2_2 = Votum(state='scheduled', number=2)
    votum_2_3 = Votum(state='scheduled', number=3)
    agenda_item_1.vota.append(votum_1_2)
    agenda_item_1.vota.append(votum_1_1)
    agenda_item_2.vota.append(votum_2_2)
    agenda_item_2.vota.append(votum_2_3)
    agenda_item_2.vota.append(votum_2_1)
    assembly.agenda_items.append(agenda_item_2)
    assembly.agenda_items.append(agenda_item_1)
    yield assembly


def test_models(session, assembly):
    # create models
    session.add(assembly)
    session.flush()
    session.expire(assembly)

    # test ordering
    assert assembly.agenda_items[0].number == 1
    assert assembly.agenda_items[0].vota[0].number == 1
    assert assembly.agenda_items[0].vota[1].number == 2
    assert assembly.agenda_items[1].number == 2
    assert assembly.agenda_items[1].vota[0].number == 1
    assert assembly.agenda_items[1].vota[1].number == 2
    assert assembly.agenda_items[1].vota[2].number == 3

    # test inherited properties
    assert assembly.agenda_items[0].date == date(2023, 5, 7)
    assert assembly.agenda_items[1].date == date(2023, 5, 7)
    assert assembly.agenda_items[0].vota[0].date == date(2023, 5, 7)
    assert assembly.agenda_items[0].vota[1].date == date(2023, 5, 7)
    assert assembly.agenda_items[1].vota[0].date == date(2023, 5, 7)
    assert assembly.agenda_items[1].vota[1].date == date(2023, 5, 7)
    assert assembly.agenda_items[1].vota[2].date == date(2023, 5, 7)
    assert assembly.agenda_items[0].vota[0].agenda_item_number == 1
    assert assembly.agenda_items[0].vota[1].agenda_item_number == 1
    assert assembly.agenda_items[1].vota[0].agenda_item_number == 2
    assert assembly.agenda_items[1].vota[1].agenda_item_number == 2
    assert assembly.agenda_items[1].vota[2].agenda_item_number == 2

    # test stamping
    assert assembly.last_modified is None
    assembly.stamp()
    assert assembly.last_modified is not None

    # test multiline agenda item title
    assert assembly.agenda_items[0].title_parts == []
    assembly.agenda_items[0].title = '   \n Lorem\r   ipsum\r\n '
    assert assembly.agenda_items[0].title_parts == ['Lorem', 'ipsum']

    # delete
    session.delete(assembly)
    assert session.query(AgendaItem).count() == 0
    assert session.query(Assembly).count() == 0
    assert session.query(Votum).count() == 0
