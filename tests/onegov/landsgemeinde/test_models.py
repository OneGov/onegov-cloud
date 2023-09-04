from datetime import date
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import Votum


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

    assert assembly.agenda_items[0].last_modified is None
    assembly.agenda_items[0].stamp()
    assert assembly.agenda_items[0].last_modified is not None

    # test multiline agenda item title
    assert assembly.agenda_items[0].title_parts == []
    assembly.agenda_items[0].title = '   \n Lorem\r   ipsum\r\n '
    assert assembly.agenda_items[0].title_parts == ['Lorem', 'ipsum']

    # delete
    session.delete(assembly)
    assert session.query(AgendaItem).count() == 0
    assert session.query(Assembly).count() == 0
    assert session.query(Votum).count() == 0
