from datetime import datetime
from lxml import etree
from onegov.core.utils import module_path
from onegov.event.utils import GuidleExportData
from pytest import mark
from sedate import replace_timezone


def tzdatetime(year, month, day, hour, minute, seconds=0, microseconds=0):
    return replace_timezone(
        datetime(year, month, day, hour, minute, seconds, microseconds),
        timezone='Europe/Zurich'
    )


@mark.parametrize("xml", [
    module_path('onegov.event', 'tests/fixtures/guidle.xml'),
])
def test_import_guidle(session, xml):
    offers = list(GuidleExportData(etree.parse(xml)).offers())
    assert len(offers) == 1

    assert offers[0].uid == '551262854'
    assert offers[0].title == "Theatervorstellung"
    assert offers[0].description == (
        "Lorem ipsum\n\n"
        "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam "
        "nonumy eirmod tempor invidunt ut labore et dolore magna "
        "aliquyam.\n\n"
        "anschliessend Apéro\n\n"
        "1-Tages- oder 2-Tagespass erhältlich\n\n"
        "www.theatermenzingen.ch"
    )
    assert offers[0].organizer == (
        "Theatervereinigung Menzingen, Peter Muster, "
        "peter.muster@theatermenzingen.ch, +41 41 755 35 46"
    )
    assert offers[0].location == (
        "Zentrum Schützenmatt, Luegetenstrasse 3, 6313 Menzingen"
    )
    assert int(offers[0].coordinates.lat) == 47
    assert int(offers[0].coordinates.lon) == 8
    assert offers[0].tags() == (
        {'Konzert Pop / Rock / Jazz', 'Kulinarik'},
        set()
    )
    assert offers[0].tags({'Konzert Pop / Rock / Jazz': 'Konzert'}) == (
        {'Konzert'}, {'Kulinarik'}
    )

    schedules = list(offers[0].schedules())
    assert len(schedules) == 4

    assert schedules[0].start == tzdatetime(2018, 10, 26, 20, 0)
    assert schedules[0].end == tzdatetime(2018, 10, 26, 22, 30)
    assert schedules[0].recurrence == (
        'RRULE:FREQ=WEEKLY;BYDAY=TU,FR,SA;UNTIL=20181104T0000Z'
    )

    assert schedules[1].start == tzdatetime(2018, 10, 28, 17, 0)
    assert schedules[1].end == tzdatetime(2018, 10, 28, 23, 59, 59, 999999)
    assert schedules[1].recurrence == ''

    assert schedules[2].start == tzdatetime(2018, 6, 15, 8, 0)
    assert schedules[2].end == tzdatetime(2018, 6, 15, 23, 59, 59, 999999)
    assert schedules[2].recurrence == (
        'RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU;UNTIL=20181016T0000Z'
    )

    assert schedules[3].start == tzdatetime(2018, 8, 18, 0, 0)
    assert schedules[3].end == tzdatetime(2018, 8, 18, 23, 59, 59, 999999)
    assert schedules[3].recurrence == (
        'RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU;UNTIL=20181101T0000Z'
    )
