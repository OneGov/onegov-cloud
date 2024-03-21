from datetime import date
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import PersonFunctionSuggestion
from onegov.landsgemeinde.models import PersonNameSuggestion
from onegov.landsgemeinde.models import PersonPlaceSuggestion
from onegov.landsgemeinde.models import PersonPoliticalAffiliationSuggestion
from onegov.landsgemeinde.models import Votum
from onegov.people import Person


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


def test_suggestions(session):

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
