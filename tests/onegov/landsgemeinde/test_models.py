from __future__ import annotations

from datetime import date
from datetime import time
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import PersonFunctionSuggestion
from onegov.landsgemeinde.models import PersonNameSuggestion
from onegov.landsgemeinde.models import PersonPlaceSuggestion
from onegov.landsgemeinde.models import PersonPoliticalAffiliationSuggestion
from onegov.landsgemeinde.models import Votum
from onegov.people import Person


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.landsgemeinde.models import Assembly
    from sqlalchemy.orm import Session


def test_models(session: Session, assembly: Assembly) -> None:
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

    agenda_item = assembly.agenda_items[0]
    votum = agenda_item.vota[0]

    # test stamping
    assert assembly.last_modified is None
    assert agenda_item.last_modified is None
    assembly.stamp()
    agenda_item.stamp()
    # undo mypy narrowing
    assembly = assembly
    agenda_item = agenda_item
    assert assembly.last_modified is not None
    assert agenda_item.last_modified is not None

    # test starting
    assert assembly.start_time is None
    assert agenda_item.start_time is None
    assert votum.start_time is None
    assembly.start()
    agenda_item.start()
    votum.start()
    # undo mypy narrowing
    assembly = assembly
    agenda_item = agenda_item
    votum = votum
    assert agenda_item.start_time is not None
    assert votum.start_time is not None

    # test multiline agenda item title
    assert agenda_item.title_parts == []
    agenda_item.title = '   \n Lorem\r   ipsum\r\n '
    assert agenda_item.title_parts == ['Lorem', 'ipsum']

    # test calculate timestamps
    assembly.start_time = None
    agenda_item.start_time = None
    votum.start_time = None
    assert agenda_item.calculated_timestamp is None
    assert votum.calculated_timestamp is None

    assembly.start_time = time(10, 1, 5)
    assert agenda_item.calculated_timestamp is None
    assert votum.calculated_timestamp is None

    agenda_item.start_time = time(11, 10, 7)
    votum.start_time = time(12, 11, 5)
    assert agenda_item.calculated_timestamp == '1h9m2s'
    assert votum.calculated_timestamp == '2h10m'

    assembly.start_time = None
    assert agenda_item.calculated_timestamp is None
    assert votum.calculated_timestamp is None

    # test video urls
    assert agenda_item.video_url is None
    assert votum.video_url is None

    assembly.video_url = 'url'
    assert agenda_item.video_url == 'url'
    assert votum.video_url == 'url'

    assembly.start_time = time(10, 1, 5)
    assert agenda_item.video_url == 'url?start=4142'
    assert votum.video_url == 'url?start=7800'

    agenda_item.video_timestamp = '1m'
    votum.video_timestamp = '1m'
    assert agenda_item.video_url == 'url?start=60'
    assert votum.video_url == 'url?start=60'

    assembly.video_url = 'url?x=1'
    assert agenda_item.video_url == 'url?x=1&start=60'
    assert votum.video_url == 'url?x=1&start=60'

    assembly.start_time = None
    agenda_item.video_timestamp = 'foo'
    votum.video_timestamp = 'foo'
    assert agenda_item.video_url == 'url?x=1'
    assert votum.video_url == 'url?x=1'

    # delete
    session.delete(assembly)
    assert session.query(AgendaItem).count() == 0
    assert session.query(Assembly).count() == 0
    assert session.query(Votum).count() == 0


def test_suggestions(session: Session) -> None:

    # no data yet
    assert PersonNameSuggestion(session).query() == []
    assert PersonNameSuggestion(session, 're').query() == []
    assert PersonFunctionSuggestion(session).query() == []
    assert PersonFunctionSuggestion(session, 'in').query() == []
    assert PersonPlaceSuggestion(session).query() == []
    assert PersonPlaceSuggestion(session, 'dt').query() == []
    assert PersonPoliticalAffiliationSuggestion(session).query() == []
    assert PersonPoliticalAffiliationSuggestion(session, 'p').query() == []

    # add people
    for (
        first_name, last_name,
        function, profession,
        postal_code_city, location_code_city,
        parliamentary_group, political_party
    ) in (
        (
            '', '',
            '', '',
            '', '',
            '', ''
        ),
        (
            'Hyacinth', 'Eustace',
            None, None,
            None, None,
            'FDP', 'jFDP'
        ),
        (
            'Israel', 'Asa',
            None, 'Landwirt',
            'Kitzbruck', '',
            '', ''
        ),
        (
            'Minos', 'Vidar',
            'Regierungsrat', '',
            'Kitzbruck', 'Hengedorf',
            'FDP', 'FDP'
        ),
        (
            'Nicolai', 'Koios',
            '', '',
            'Hengestadt', '',
            '', ''
        ),
        (
            'Annette', 'Helena',
            'Regierungsrätin', '',
            None, None,
            '', ''
        ),
        (
            'Ireneo', 'Madina',
            None, None,
            'Terschlag', '',
            'Grüne', ''
        ),
        (
            'Hammurabi', 'Gavril',
            None, '',
            '', '',
            '', ''
        ),
    ):
        session.add(
            Person(
                first_name=first_name,
                last_name=last_name,
                function=function,
                profession=profession,
                postal_code_city=postal_code_city,
                location_code_city=location_code_city,
                parliamentary_group=parliamentary_group,
                political_party=political_party
            )
        )

    # add vota
    assemblies = [
        Assembly(state='completed', date=date(2020, 5, 1)),
        Assembly(state='completed', date=date(1980, 5, 1))
    ]
    assemblies[0].agenda_items.append(AgendaItem(state='completed', number=1))
    assemblies[1].agenda_items.append(AgendaItem(state='completed', number=1))
    for assembly in assemblies:
        session.add(assembly)
    session.flush()

    for (index, name, function, place, political_affiliation) in (
        (0, 'Óskar Hilarion', '', 'Terschlag', 'FDP'),
        (0, 'Hans Issa', 'Landrat', 'Vellzach', 'SP'),
        (0, None, None, 'Mensee', 'SVP'),
        (1, 'Germana Enyinnaya', 'Landrätin', 'Terschlag', 'Mitte'),
        (1, 'Gabriel Kinneret', '', 'Blankenstadt', 'FDP'),
        (1, '', '', '', 'Mitte'),
        (1, 'Nele Idella', '', 'Blankenstadt', 'SP'),
    ):
        session.add(
            Votum(
                state='completed',
                number=1,
                agenda_item_id=assemblies[index].agenda_items[0].id,
                person_name=name,
                person_function=function,
                person_place=place,
                person_political_affiliation=political_affiliation
            )
        )
    session.flush()

    # test names
    assert PersonNameSuggestion(session).query() == []
    assert PersonNameSuggestion(session, 'a').query() == [
        'Annette Helena',
        'Hammurabi Gavril',
        'Hyacinth Eustace',
        'Ireneo Madina',
        'Israel Asa',
        'Hans Issa',
        'Óskar Hilarion',
        'Gabriel Kinneret',
        'Germana Enyinnaya',
        'Nele Idella',
    ]
    assert PersonNameSuggestion(session, 're').query() == [
        'Ireneo Madina',
        'Gabriel Kinneret'
    ]

    # test functions
    assert PersonFunctionSuggestion(session).query() == []
    assert PersonFunctionSuggestion(session, 'n').query() == [
        'Landwirt',
        'Regierungsrat',
        'Regierungsrätin',
        'Landrat',
        'Landrätin',
    ]
    assert PersonFunctionSuggestion(session, 'in').query() == [
        'Regierungsrätin',
        'Landrätin'
    ]

    # test places
    assert PersonPlaceSuggestion(session).query() == []
    assert PersonPlaceSuggestion(session, 'e').query() == [
        'Hengedorf',
        'Hengestadt',
        'Terschlag',
        'Mensee',
        'Vellzach',
        'Blankenstadt',
    ]
    assert PersonPlaceSuggestion(session, 'dt').query() == [
        'Hengestadt',
        'Blankenstadt',
    ]

    # test political affiliation
    assert PersonPoliticalAffiliationSuggestion(session).query() == []
    assert PersonPoliticalAffiliationSuggestion(session, 's').query() == [
        'SP', 'SVP',
    ]
    assert PersonPoliticalAffiliationSuggestion(session, 'p').query() == [
        'FDP', 'jFDP', 'SP', 'SVP',
    ]
