from __future__ import annotations

import pytest

from datetime import datetime
from onegov.fsi.ims_import import (
    InconsistencyError,
    parse_completed,
    parse_courses,
    parse_date,
    parse_email,
    parse_events,
    parse_persons,
    parse_status,
    validate_integer,
)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path


def _csv(tmp_path: Path, name: str, header: str, *rows: str) -> str:
    path = tmp_path / name
    content = '\r\n'.join((header, *rows)) + '\r\n'
    path.write_bytes(content.encode('iso-8859-1'))
    return str(path)


# --- pure helpers -------------------------------------------------------


def test_parse_email() -> None:
    assert parse_email(' User.A@Example.org ') == 'user.a@example.org'
    # .local suffix is stripped
    assert parse_email('ua@example.org.local') == 'ua@example.org'
    # empty becomes None
    assert parse_email('   ') is None


def test_parse_date() -> None:
    parsed = parse_date('2020-01-02')
    assert isinstance(parsed, datetime)
    assert (parsed.year, parsed.month, parsed.day) == (2020, 1, 2)
    assert parsed.tzinfo is not None

    # empty returns the default
    assert parse_date('') is None
    assert parse_date(None, default='x') == 'x'


def test_parse_status() -> None:
    assert parse_status('Abgeschlossen') == 'confirmed'
    assert parse_status('Abgesagt') == 'canceled'
    assert parse_status('Erfasst') == 'created'
    with pytest.raises(KeyError):
        parse_status('Unknown')


def test_validate_integer() -> None:
    assert validate_integer('42') == 42
    assert validate_integer('') == 0
    assert validate_integer(None) == 0
    assert validate_integer('', default=5) == 5
    with pytest.raises(ValueError):
        validate_integer('', treat_none_as_default=False)


def test_parse_completed() -> None:
    assert parse_completed('J') is True
    assert parse_completed(None) is True
    assert parse_completed('N') is False


def test_inconsistency_error() -> None:
    error = InconsistencyError('bad', 'persons.txt', 7)
    assert str(error) == 'persons.txt:7 - bad'


# --- parse_persons ------------------------------------------------------


def test_parse_persons(tmp_path: Path) -> None:
    path = _csv(
        tmp_path, 'persons.txt',
        'obj_id,p_email,p_userid,p_vorname,p_name',
        '100,Anna@example.org,ua,Anna,Alpha',
        '200,Bob@example.org,ub,Bob,Beta',
        # duplicate obj_id is ignored (setdefault)
        '100,other@example.org,ux,Other,Name',
    )

    persons = parse_persons(path)
    assert set(persons) == {'100', '200'}
    assert persons['100'] == {
        'obj_id': '100',
        'email': 'anna@example.org',
        'code': 'ua',
        'first_name': 'Anna',
        'last_name': 'Alpha',
    }


# --- parse_courses ------------------------------------------------------


def test_parse_courses(tmp_path: Path) -> None:
    path = _csv(
        tmp_path, 'courses.txt',
        'vorgangsnr,kurzbeschreibung,detailbeschreibung',
        '5,Security Course,<p>Details</p>',
    )

    errors, courses = parse_courses(path)
    assert errors == {}
    assert set(courses) == {'5'}
    assert courses['5'].name == 'Security Course'
    assert 'Details' in courses['5'].description


# --- parse_events -------------------------------------------------------


def test_parse_events(tmp_path: Path) -> None:
    _, courses = parse_courses(_csv(
        tmp_path, 'courses.txt',
        'vorgangsnr,kurzbeschreibung,detailbeschreibung',
        '5,Security Course,desc',
    ))

    header = (
        'proc_id_kv,kurs_von,kurs_bis,buchungsstatus,teilnehmer_min,'
        'teilnehmer_max,kurslokal,referent_name,referent_firma,status,proc_id'
    )
    path = _csv(
        tmp_path, 'events.txt',
        header,
        '5,2020-01-01,2020-01-02,Gebucht,1,10,Room A,Dr X,ACME,Erfasst,900',
        # no booking and no dates -> skipped
        '5,,,Keine Buchung,1,10,Room A,Dr X,ACME,Erfasst,901',
    )

    errors, events = parse_events(path, courses)
    assert errors == {}
    assert set(events) == {'900'}
    event = events['900']
    assert event.location == 'Room A'
    assert event.min_attendees == 1
    assert event.max_attendees == 10
    assert event.status == 'created'
    assert event.presenter_company == 'ACME'


def test_parse_events_defaults_missing_presenter(tmp_path: Path) -> None:
    _, courses = parse_courses(_csv(
        tmp_path, 'courses.txt',
        'vorgangsnr,kurzbeschreibung,detailbeschreibung',
        '5,Security Course,desc',
    ))

    header = (
        'proc_id_kv,kurs_von,kurs_bis,buchungsstatus,teilnehmer_min,'
        'teilnehmer_max,kurslokal,referent_name,referent_firma,status,proc_id'
    )
    path = _csv(
        tmp_path, 'events.txt',
        header,
        # empty end date -> end defaults to start; empty presenter -> defaults
        '5,2020-01-01,,Gebucht,,,Room A,,,Abgeschlossen,900',
    )

    _, events = parse_events(path, courses)
    event = events['900']
    assert event.start == event.end
    assert event.presenter_name == 'Unbekannter Referent'
    assert event.presenter_company == 'Unbekannte Firma'
    assert event.min_attendees == 0
    assert event.status == 'confirmed'
