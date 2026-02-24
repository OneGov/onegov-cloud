"""
Dateien:

- Kurse: Die Liste der Kurse
- Personen -> importiert aus ldap
- Teilnehmer: repräsentiert die Anmeldungen mit referenz zu
  Personen und Durchführungen
- Ausführungen: die Listen der Durchführungen.


Verlinkungen

- Teilnehmer.TEILNEHMER_ID is ForeignKey für Personen.OBJ_ID

Im folgenden eine Beschreibung der Beobachtungen zu den Files

Personen.txt:

(Daten sind sortiert nach Nachname/Vorname)

- Es gibt Email-Adressen wie user@sg.ch.local, und dann in den Anmeldungen
  ohne .local.
- Was bedeutet das Feld P_VALID_TILL? Relevant?
- es gibt viele Einträge ohne email und/oder Kürzel (P_USERID), z.B. Zeilen
- es gibt viele fehlende Vornamen/Nachnamen (evtl auffindbar in Teilnehmer.txt)
- Neu erstellte Einträge mit gleicher Email und sonst gleichen Informationen:
  Beispiel Zeilen 2215/2216. Wie vorgehen, wenn es alte Anmeldungen zu Kursen
  gibt, die auf den alten Eintrag zeigen?

Fragen:

- Sind in Personen.txt auch externe Benutzer erfasst?
- Kann ich externe Benutzer über den Eintrag P_VERWALTUNG identifizieren?
  Hier gibt es

  - [spezielle/ungültige/fehlerhafte]
  - Dritte
  - Gemeinde
  - Kantonale Verwaltung Zug
  - Staatskanzlei

  Welche von denen sind in unserem LDAP? Das sollte ich in etwa wissen.

- Was ist zu tun mit 'alten' Benutzern? Und wie definieren wir alte Benutzer?
- Ist ein alter Benutzer, der sich nicht mehr einloggen kann?
- Inwieweit sollen 'alte' Benutzer noch in die Datenbank rein?
- Sollen damit Anmeldungen von 'alten' Benutzern nicht importiert werden?

Ausführungen.txt:

- Wir haben Start und/oder Ende einer Durchführung fehlend, bei verschiedenen
  manchmal mit BUCHUNGSTATUS = Keine Buchung, kann aber auch
  Erfasst oder Abgesagt sein, ein Datum muss in der neuen Datenbank
  eingetragen werden.

- Fehlende Namen der Kursleitung: Entweder 'Unbekannter Referent' als default
  oder Datenbank abändern (in Formularen weiterhin Pflichtfeld).

Teilnehmer.txt

- Field ANWESEND oft leer, soll Ja oder Nein gewählt werden?
- Einträge ohne TEILNEHMER_ID (Link zu Personen.txt) sind externe Benutzer
  z.B.

FAZIT

Vorgeschlagenes Vorgehen:

Die "single source of truth" bildet das bereits umegesetzte Verzeichnis
der gültigen Benutzer aus dem LDAP kombiniert mit den weiteren Verzeichnissen.
Es sollen nur Anmeldungen von mittels LDAP identifizierbaren Personen
importiert werden.

Es werden nicht importiert:

- Personen, ohne Kürzel und Email sowie deren alte Anmeldungen
- Durchführungen mit BUCHUNGS_STATUS = Keine Buchung and Start/Ende fehlend
  werden auch nicht mehr importiert.
- Durchführungen ohne Start UND Ende unabhängig von Status

Vervollständigungen

- .local in Email-Adressen wird herausgenommen
- Fehlender Wert für ANWESEND bei alten Anmeldungen wird mit JA gefüllt.
- Referent Kurs: Standard-Wert einfügen "Unbekannter Referent" sofern fehlend

Gemäss dem code (src/onegov/fsi/ims_import.py:368) gibt es keine Benutzer
in Personen.txt die weder email noch code haben und von den Teilnehmer.txt
her aus vervollständigt werden müssten.

Anmeldungen in Teilnehmer.txt die keine Referenz zu Personen.txt haben,
wurden berücksichtigt, sofern eine Email vorlag.

"""
from __future__ import annotations

import click
import dateutil.parser
from collections import OrderedDict, defaultdict
from datetime import datetime
from sedate import replace_timezone
from sqlalchemy import cast, Date
from uuid import uuid4

from onegov.core.csv import CSVFile
from onegov.core.html import sanitize_html
from onegov.fsi.collections.subscription import SubscriptionsCollection
from onegov.fsi.models import CourseEvent, Course, CourseSubscription
from onegov.fsi.models.course_notification_template import (
    InfoTemplate, SubscriptionTemplate, CancellationTemplate, ReminderTemplate)
from onegov.user import User


from typing import TypeVarTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.core.csv import DefaultRow
    from onegov.fsi.models import CourseAttendee
    from onegov.fsi.models.course_event import EventStatusType
    from onegov.fsi.request import FsiRequest
    from sqlalchemy.orm import Session
    from typing import TypedDict, NotRequired
    from typing_extensions import TypeVar
    from uuid import UUID

    T = TypeVar('T')
    DefaultT = TypeVar('DefaultT', default=None)

    class SubscriptionDict(TypedDict):
        course_event_id: UUID
        completed: bool

    class PersonDict(TypedDict):
        obj_id: str
        email: str | None
        code: str | None
        first_name: str | None
        last_name: str | None
        subscriptions: NotRequired[list[SubscriptionDict]]

    class UserDict(TypedDict):
        id: UUID
        email: str | None
        organisation: str | None
        first_name: str | None
        last_name: str | None
        subscriptions: list[SubscriptionDict]

Ts = TypeVarTuple('Ts')


class InconsistencyError(BaseException):

    def __init__(
        self,
        msg: str,
        file: str,
        rownumber: int | None = None
    ) -> None:
        self.msg = msg
        self.file = file
        self.rownumber = rownumber

    def __str__(self) -> str:
        return f'{self.file}:{self.rownumber} - {self.msg}'


def parse_email(email: str) -> str | None:
    # some mail lack .org
    email = email.strip().replace('.local', '').lower()
    if not email:
        return None
    if email[-3:] != '.ch' and email[-3:] == '@ẑg':
        email += '.ch'
    return email


def parse_date(
    val: str | None,
    # NOTE: Seems like PEP-696 does not allow assigning a TypeVar to its
    #       default value yet, this should probably be allowed
    default: DefaultT = None  # type:ignore[assignment]
) -> datetime | DefaultT:
    if not val:
        return default
    date_ = dateutil.parser.parse(val)
    return replace_timezone(date_, 'UTC')


def parse_status(val: str) -> EventStatusType:
    mapping: dict[str, EventStatusType] = {
        'Abgeschlossen': 'confirmed',
        'Abgesagt': 'canceled',
        'Erfasst': 'created'
    }
    return mapping[val]


def validate_integer(
    val: str | None,
    treat_none_as_default: bool = True,
    default: int = 0
) -> int:
    if not val:
        if treat_none_as_default:
            return default
        raise ValueError(f'Empty value: {val}')
    return int(val)


def with_open(
    func: Callable[[CSVFile[DefaultRow], *Ts], T]
) -> Callable[[str, *Ts], T]:
    def _read(filename: str, /, *args: *Ts) -> T:
        with open(filename, 'rb') as f:
            file = CSVFile(
                f,
                dialect='excel',
                encoding='iso-8859-1'
            )
            return func(file, *args)
    return _read


@with_open
def import_teacher_data(
    csvfile: CSVFile[DefaultRow],
    request: FsiRequest,
    clean: bool = False
) -> None:

    session = request.session

    sgk = session.query(Course).filter_by(
        name='Sicherheitsgrundkurs (SGK)').one()

    subscriptions = SubscriptionsCollection(session)
    total_lines = 0
    matched_count = 0
    deleted_count = 0

    for ix, line in enumerate(csvfile.lines):
        total_lines += 1
        email = line.emailadresse.lower()
        course_name = line.kursbezeichnung
        if 'Sicherheitsgrundkurs' not in course_name:
            continue

        course_date = datetime.strptime(line.kursdatum, '%d.%m.%Y').date()
        confirmed = line.besucht == 'J' and True or False

        matched_teacher = session.query(User).filter_by(username=email).first()
        if not matched_teacher:
            click.echo(f'{email} not found')
            continue

        assert hasattr(matched_teacher, 'attendee')
        matched_event = sgk.events.filter(
            cast(CourseEvent.start, Date) == course_date
        ).order_by(CourseEvent.start).first()

        if matched_event:
            if not confirmed:
                click.echo(f'{email} for {course_date!s} not confirmed')
            # click.echo(f'Found {email} in database and event that day')
            matched_count += 1
            if not clean:
                subscriptions.add(
                    course_event_id=matched_event.id,
                    attendee_id=matched_teacher.attendee.id,
                    event_completed=confirmed
                )
            else:
                attendee_id = matched_teacher.attendee.id
                subs = session.query(CourseSubscription).filter(
                    CourseSubscription.course_event_id == matched_event.id,
                    CourseSubscription.attendee_id == attendee_id
                ).first()
                if subs:
                    deleted_count += 1
                    session.delete(subs)

    click.echo(f'Total lines: {total_lines}')
    click.echo(f'Matched emails/events: {matched_count}')
    if clean:
        click.echo(f'Deleted {deleted_count} subscriptions')


def parse_completed(val: str | None) -> bool:
    return val != 'N'


@with_open
def parse_persons(csvfile: CSVFile[DefaultRow]) -> dict[str, PersonDict]:
    """Pure extracting information"""
    persons: dict[str, PersonDict] = OrderedDict()
    click.echo('-- parse_persons --')
    for line in csvfile.lines:

        obj_id = line.obj_id
        assert obj_id
        # valid_till = parse_date(line.p_valid_till)

        persons.setdefault(obj_id, {
            'obj_id': obj_id,
            'email': parse_email(line.p_email),
            'code': line.p_userid,
            'first_name': line.p_vorname,
            'last_name': line.p_name,
        })
    return persons


@with_open
def parse_courses(
    csvfile: CSVFile[DefaultRow]
) -> tuple[dict[int, str], dict[str, Course]]:
    errors = OrderedDict()
    courses = OrderedDict()
    click.echo('-- parse_courses --')

    for line in csvfile.lines:
        try:
            courses[line.vorgangsnr] = Course(
                id=uuid4(),
                name=line.kurzbeschreibung,
                description=sanitize_html(line.detailbeschreibung)
            )
        except Exception as e:
            errors[line.rownumber] = e.args[0]
            continue

    return errors, courses


@with_open
def parse_events(
    csvfile: CSVFile[DefaultRow],
    courses: dict[str, Course]
) -> tuple[dict[int, str], dict[str, CourseEvent]]:
    events = OrderedDict()
    errors = OrderedDict()
    click.echo('-- parse_events --')
    for line in csvfile.lines:

        # Block accepts empty end values, but fails if the start is not set
        parent_course = courses[line.proc_id_kv]
        if not parent_course:
            click.echo(
                f'Skipping {line.rownumber}: parent id {line.proc_id_kv} '
                f'not found in Personen.txt'
            )
            continue

        date_lacking = not line.kurs_von or not line.kurs_bis
        if line.buchungsstatus == 'Keine Buchung' and date_lacking:
            click.echo(
                f'Skipping line {line.rownumber}: '
                f'status: Buchungsstatus = Keine Buchung and lacking date'
            )
            continue

        try:
            start = parse_date(line.kurs_von)
            assert start is not None
        except Exception as e:
            errors[line.rownumber] = e.args[0]
            click.echo(f'Skipping {line.rownumber}: {e.args[0]}')
            continue
        try:
            # Setting end to start in case end is empty
            end = parse_date(line.kurs_bis, default=start)
        except TypeError:
            click.echo(f'{line.rownumber}: invalid date, setting end = start')
            end = start

        default_name = 'Unbekannter Referent'
        default_company = 'Unbekannte Firma'
        min_att = validate_integer(line.teilnehmer_min)
        max_att = validate_integer(line.teilnehmer_max)

        event = CourseEvent(
            id=uuid4(),
            course_id=parent_course.id,
            location=line.kurslokal,
            start=start,
            end=end,
            presenter_name=line.referent_name or default_name,
            presenter_company=line.referent_firma or default_company,
            min_attendees=min_att,
            max_attendees=max_att,
            status=parse_status(line.status),
        )
        events[line.proc_id] = event
    return errors, events


@with_open
def parse_subscriptions(
    csvfile: CSVFile[DefaultRow],
    persons: dict[str, PersonDict],
    events: dict[str, CourseEvent]
) -> tuple[dict[int, str], dict[str, PersonDict], dict[str, UserDict]]:
    """

    :param csvfile:
    :param persons: dict of dicts of person records
    :param events: dict of CourseEvent classes
    :return: subscriptions within persons and within maybe_external_in_ldap
    """
    click.echo('-- parse_subscriptions --')

    # The selection of valid subscriptions/subscriptions
    errors: dict[int, str] = OrderedDict()
    maybe_external_in_ldap: dict[str, UserDict] = OrderedDict()
    emails_by_teilnehmer_id = defaultdict(list)

    # new_emails_for_existing = defaultdict(list)

    for line in csvfile.lines:
        teilnehmer_id = line.teilnehmer_id
        course_event = events.get(line.proc_id)
        completed = parse_completed(line.anwesend)

        if not course_event:
            click.echo(
                f'Skipping {line.rownumber}: drop since no course event'
            )
            continue

        email = parse_email(line.teilnehmer_email)

        if teilnehmer_id:
            # Deal with the persons object
            person_obj = persons.get(line.teilnehmer_id)

            if not person_obj:
                click.echo(f'Skipping {line.rownumber}: orphaned subscription')
                # skip orphaned subscriptions
                continue

            # Analyze possible identifiers
            code = person_obj['code']
            current_email = person_obj['email']
            # first_name, last_name from Persons
            first_name = person_obj['first_name']
            last_name = person_obj['last_name']
            complete_record = all((current_email, code, first_name, last_name))

            # skip subscriptions for persons without email and code
            if not current_email and not code:
                click.echo(
                    f'Skipping {line.rownumber}: '
                    f'person obj without email and code'
                )
                continue

            subscriptions = person_obj.setdefault(
                'subscriptions', [])

            if code:
                # Add to valid subscriptions
                subscriptions.append({
                    'course_event_id': course_event.id,
                    'completed': completed
                })
                continue

            if current_email:
                # just current_email
                if current_email != email:
                    # Assert full profile of the record in Personen.txt
                    assert complete_record
                subscriptions.append({
                    'course_event_id': course_event.id,
                    'completed': completed
                })
                continue

            if email:
                # Just a check, empty will be assert beneath
                emails_by_teilnehmer_id[teilnehmer_id].append(email)

        elif line.teilnehmer_firma == 'Intern':
            click.echo(
                f'Skipping {line.rownumber}: '
                f'Firma intern but no link to Persons'
            )
            continue
        else:
            # no teilnehmer_id so is external from a school or elsewhere
            first_name = line.teilnehmer_vorname
            last_name = line.teilnehmer_nachname

            if not (email and first_name and last_name):
                click.echo(
                    f'Skipping {line.rownumber}: '
                    'Subscription misses one of '
                    'email, firstname or lastname'
                )
                continue

            external = maybe_external_in_ldap.setdefault(email, {
                'id': uuid4(),
                'first_name': first_name,
                'last_name': last_name,
                'organisation': line.teilnehmer_firma,
                'subscriptions': [],
                'email': email
            })
            external['subscriptions'].append({
                'course_event_id': course_event.id,
                'completed': completed
            })

    assert not emails_by_teilnehmer_id

    return errors, persons, maybe_external_in_ldap


def map_persons_to_known_ldap_user(
    person_record: PersonDict | UserDict,
    session: Session
) -> CourseAttendee | None:
    """
    Since the exported persons table contains records without email
    from various sources, we have to try to map it to an existing record
    or create a new one.

    The ldap fetched users have an attendee created with
    first_name, last_name and email set on the attendee as well.

    Returns an attendee or None
    """
    code = person_record.get('code', None)
    email = person_record['email']

    if code:
        user = session.query(User).filter_by(source_id=code).first()
        if user:
            if email and user.username != email:
                # set email to most up-to-date
                email = user.username

            assert hasattr(user, 'attendee')
            if not user.attendee:
                raise InconsistencyError(
                    f'{email} - {code}: user should have an attendee',
                    'Personen.txt',
                )
            return user.attendee
        click.echo(f'LDAP CODE: {code} not found, Email {email} not searched')
    elif email:
        user = session.query(User).filter_by(username=email).first()
        if user:
            assert hasattr(user, 'attendee')
            if not user.attendee:
                raise InconsistencyError(
                    f'{email}: user should have an attendee',
                    'Personen.txt',
                )
            return user.attendee
        click.echo(f'LDAP EMAIL: {email} not found')

    else:
        identifier = person_record.get('obj_id') or email
        click.echo(f'No identifier for user with OBJ_ID {identifier}')
    return None


def parse_ims_data(
    subscriptions_file: str,
    events_file: str,
    courses_file: str,
    persons_file: str,
) -> tuple[
    dict[str, dict[int, str]],
    dict[str, PersonDict] | None,
    dict[str, Course] | None,
    dict[str, CourseEvent] | None,
    dict[str, UserDict] | None
]:
    gathered_errors = {}

    # raw extraction
    raw_persons = parse_persons(persons_file)

    errors, courses = parse_courses(courses_file)

    if errors:
        gathered_errors['parse_courses'] = errors
        return gathered_errors, None, None, None, None

    errors, events = parse_events(events_file, courses)
    if errors:
        gathered_errors['parse_events'] = errors
        return gathered_errors, None, None, None, None

    errors, persons, possible_ldap_users = parse_subscriptions(
        subscriptions_file, raw_persons, events)

    if errors:
        gathered_errors['parse_subscriptions'] = errors

    return gathered_errors, persons, courses, events, possible_ldap_users


def import_ims_data(
    session: Session,
    persons: dict[str, PersonDict],
    courses: dict[str, Course],
    events: dict[str, CourseEvent],
    possible_ldap_users: dict[str, UserDict]
) -> dict[str, int]:

    click.echo('-- Import IMS DATA to database with LDAP --')

    statistics = {
        'LDAP_found': 0,
        'LDAP_not_found': 0,
        'external_found': 0,
        'external_not_found': 0,
    }

    session.add_all(courses.values())
    for event in events.values():
        session.add(event)
        data = {'course_event_id': event.id}
        session.add_all((
            InfoTemplate(**data),
            SubscriptionTemplate(**data),
            CancellationTemplate(**data),
            ReminderTemplate(**data)
        ))

    for person in persons.values():
        attendee = map_persons_to_known_ldap_user(person, session)
        if not attendee:
            statistics['LDAP_not_found'] += 1
            continue
        statistics['LDAP_found'] += 1
        subscriptions = person['subscriptions']
        if not subscriptions:
            continue
        session.add_all(
            CourseSubscription(
                attendee_id=attendee.id,
                course_event_id=r['course_event_id'],
                event_completed=r['completed']
            ) for r in subscriptions
        )

    for record in possible_ldap_users.values():
        attendee = map_persons_to_known_ldap_user(record, session)
        if not attendee:
            statistics['external_not_found'] += 1
            continue
        statistics['external_found'] += 1
        session.add_all(
            CourseSubscription(
                attendee_id=attendee.id,
                course_event_id=r['course_event_id']
            ) for r in record['subscriptions']
        )
    return statistics
