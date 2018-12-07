from datetime import datetime
from dateutil.parser import parse
from lxml import etree
from onegov.core.utils import module_path
from onegov.event.utils import as_rdates
from onegov.event.utils import GuidleExportData
from pytest import mark
from pytest import raises
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
    assert offers[0].last_update == "2017-10-21T22:44:12.834+02:00"
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


def test_as_rdates():
    with raises(AssertionError):
        as_rdates('RRULE:FREQ=DAILY;COUNT=1\nRDATE:20190223T000000\n')

    rrule = (
        'RRULE:FREQ=DAILY;COUNT=1\n'
        'RDATE:20190223T000000\n'
    )
    assert as_rdates(rrule, parse('2018-11-03T09:00:00+00:00')) == (
        'RDATE:2018-11-03T000000Z\n'
        'RDATE:2019-02-23T000000Z'
    )

    rrule = (
        'RRULE:FREQ=DAILY;COUNT=7\n'
        'EXDATE:20181111T000000,20181112T000000,20181113T000000,'
        '20181114T000000,20181115T000000,20181116T000000\n'
        'RDATE:20181201T000000,20190112T000000\n'
    )
    assert as_rdates(rrule, parse('2018-09-05T10:30:00+00:00')) == (
        'RDATE:2018-09-05T000000Z\n'
        'RDATE:2018-09-06T000000Z\n'
        'RDATE:2018-09-07T000000Z\n'
        'RDATE:2018-09-08T000000Z\n'
        'RDATE:2018-09-09T000000Z\n'
        'RDATE:2018-09-10T000000Z\n'
        'RDATE:2018-09-11T000000Z\n'
        'RDATE:2018-12-01T000000Z\n'
        'RDATE:2019-01-12T000000Z'
    )

    rrule = (
        'RRULE:FREQ=MONTHLY;BYDAY=-1FR;COUNT=6\n'
        'EXDATE:20180727T000000,20181224T000000,20181228T000000,'
        '20190125T000000\n'
        'RDATE:20181207T000000,20181222T000000\n'
    )
    assert as_rdates(rrule, parse('2018-08-31T07:30:00+00:00')) == (
        'RDATE:2018-08-31T000000Z\n'
        'RDATE:2018-09-28T000000Z\n'
        'RDATE:2018-10-26T000000Z\n'
        'RDATE:2018-11-30T000000Z\n'
        'RDATE:2018-12-07T000000Z\n'
        'RDATE:2018-12-22T000000Z'
    )

    rrule = (
        'RRULE:FREQ=MONTHLY;BYDAY=-1SA;COUNT=4\n'
        'EXDATE:20181027T000000,20181124T000000\n'
        'RDATE:20181110T000000,20181215T000000\n'
    )
    assert as_rdates(rrule, parse('2018-08-25T08:30:00+00:00')) == (
        'RDATE:2018-08-25T000000Z\n'
        'RDATE:2018-09-29T000000Z\n'
        'RDATE:2018-11-10T000000Z\n'
        'RDATE:2018-12-15T000000Z'
    )

    rrule = (
        'RRULE:FREQ=MONTHLY;BYDAY=+1FR;UNTIL=20181207T000000\n'
    )
    assert as_rdates(rrule, parse('2018-01-05T15:00:00+00:00')) == (
        'RDATE:2018-01-05T000000Z\n'
        'RDATE:2018-02-02T000000Z\n'
        'RDATE:2018-03-02T000000Z\n'
        'RDATE:2018-04-06T000000Z\n'
        'RDATE:2018-05-04T000000Z\n'
        'RDATE:2018-06-01T000000Z\n'
        'RDATE:2018-07-06T000000Z\n'
        'RDATE:2018-08-03T000000Z\n'
        'RDATE:2018-09-07T000000Z\n'
        'RDATE:2018-10-05T000000Z\n'
        'RDATE:2018-11-02T000000Z\n'
        'RDATE:2018-12-07T000000Z'
    )

    rrule = (
        'RRULE:FREQ=MONTHLY;BYDAY=+4SA;COUNT=5\n'
        'EXDATE:20181124T000000,20181222T000000\n'
        'RDATE:20181117T000000,20181215T000000\n'
    )
    as_rdates(rrule, parse('2018-08-25T13:00:00+00:00')) == (
        'RDATE:2018-08-25T000000Z\n'
        'RDATE:2018-09-22T000000Z\n'
        'RDATE:2018-10-27T000000Z\n'
        'RDATE:2018-11-17T000000Z\n'
        'RDATE:2018-12-15T000000Z'
    )
