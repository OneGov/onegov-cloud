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

- Es gibt Email-Addressen wie user@sg.ch.local, und dann in den Anmeldungen
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

- .local in Email-Addressen wird herausgenommen
- Fehlender Wert für ANWESEND bei alten Anmeldungen wird mit JA gefüllt.
- Referent Kurs: Standard-Wert einfügen "Unbekannter Referent" sofern fehlend

Gemäss dem code (src/onegov/fsi/ims_import.py:368) gibt es keine Benutzer
in Personen.txt die weder email noch code haben und von den Teilnehmer.txt
her aus vervollständigt werden müssten.

Anmeldungen in Teilnehmer.txt die keine Referenz zu Personen.txt haben,
wurden berücksichtigt, sofern eine Email vorlag.

"""
from collections import OrderedDict, defaultdict
from uuid import uuid4
import dateutil.parser
from sedate import replace_timezone

from onegov.core.csv import CSVFile
from onegov.fsi.models import CourseEvent, Course, CourseReservation, \
    CourseAttendee
from onegov.fsi.models.course_notification_template import InfoTemplate, \
    ReservationTemplate, CancellationTemplate, ReminderTemplate
from onegov.user import User


class InconsistencyError(BaseException):

    def __init__(self, msg, file, rownumber=None):
        self.msg = msg
        self.file = file
        self.rownumber = rownumber

    def __str__(self):
        return f'{self.file}:{self.rownumber} - {self.msg}'


def parse_email(email):
    # some mail lack .org
    email = email.strip().replace('.local', '').lower()
    if not email:
        return None
    if not email[-3:] == '.ch' and email[-3:] == '@ẑg':
        email += '.ch'
    return email


def parse_date(val, default=None):
    if not val:
        return default
    date_ = dateutil.parser.parse(val)
    return replace_timezone(date_, 'UTC')


def parse_status(val):
    mapping = {
        'Abgeschlossen': 'confirmed',
        'Abgesagt': 'canceled',
        'Erfasst': 'created'
    }
    return mapping[val]


def validate_integer(val, treat_none_as_default=True, default=0):
    if not val:
        if treat_none_as_default:
            return default
        raise ValueError(f'Empty value: {val}')
    return int(val)


def with_open(func):
    def _read(*args):
        with open(args[0], 'rb') as f:
            file = CSVFile(
                f,
                dialect='excel',
                encoding='iso-8859-1'
            )
            return func(file, *args[1:])
    return _read


def parse_completed(val):
    return False if val == 'N' else True


@with_open
def parse_persons(csvfile):
    """Pure extracting information"""
    persons = OrderedDict()
    print('-- parse_persons --')
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
def parse_courses(csvfile):
    errors = OrderedDict()
    courses = OrderedDict()
    print('-- parse_courses --')

    for line in csvfile.lines:
        try:
            courses[line.vorgangsnr] = Course(
                id=uuid4(),
                name=line.kurzbeschreibung,
                description=line.detailbeschreibung
            )
        except Exception as e:
            errors[line.rownumber] = e.args[0]
            continue

    return errors, courses


@with_open
def parse_events(csvfile, courses):
    events = OrderedDict()
    errors = OrderedDict()
    print('-- parse_events --')
    for line in csvfile.lines:

        # Block accepts empty end values, but fails if the start is not set
        parent_course = courses[line.proc_id_kv]
        if not parent_course:
            print(f'Skipping {line.rownumber}: parent id {line.proc_id_kv} '
                  f'not found in Personen.txt')
            continue

        date_lacking = not line.kurs_von or not line.kurs_bis
        if line.buchungsstatus == 'Keine Buchung' and date_lacking:
            print(f'Skipping line {line.rownumber}: '
                  f'status: Buchungsstatus = Keine Buchung and lacking date')
            continue

        try:
            start = parse_date(line.kurs_von)
        except Exception as e:
            errors[line.rownumber] = e.args[0]
            print(f'Skipping {line.rownumber}: {e.args[0]}')
            continue
        try:
            # Setting end to start in case end is empty
            end = parse_date(line.kurs_bis, default=start)
        except TypeError:
            print(f'{line.rownumber}: invalid date, setting end = start')
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
def parse_subscriptions(csvfile, persons, events):
    """

    :param csvfile:
    :param persons: dict of dicts of person records
    :param events: dict of CourseEvent classes
    :return: subscriptions within persons and within maybe_external_in_ldap
    """
    print('-- parse_subscriptions --')

    # The selection of valid subscriptions/reservations
    errors = OrderedDict()
    droppped_teilnehmer_ids = []
    maybe_external_in_ldap = OrderedDict()
    emails_by_teilnehmer_id = defaultdict(list)

    # new_emails_for_existing = defaultdict(list)

    for line in csvfile.lines:
        teilnehmer_id = line.teilnehmer_id
        course_event = events.get(line.proc_id)
        completed = parse_completed(line.anwesend)

        if not course_event:
            print(f'Skipping {line.rownumber}: drop since no course event')
            continue

        email = parse_email(line.teilnehmer_email)

        if teilnehmer_id:
            # Deal with the persons object
            person_obj = persons.get(line.teilnehmer_id)

            if not person_obj:
                print(f'Skipping {line.rownumber}: orphaned subscription')
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
                print(f'Skipping {line.rownumber}: '
                      f'person obj without email and code')
                continue

            subscriptions = person_obj.setdefault(
                'subscriptions', [])

            if code:
                # Add to valid subscriptions
                subscriptions.append(dict(
                    course_event_id=course_event.id,
                    event_completed=completed
                ))
                continue

            if current_email:
                # just current_email
                if not current_email == email:
                    # Assert full profile of the record in Personen.txt
                    assert complete_record
                subscriptions.append(dict(
                    course_event_id=course_event.id,
                    completed=completed
                ))
                continue

            if email:
                # Just a check, empty will be assert beneath
                emails_by_teilnehmer_id[teilnehmer_id].append(email)

        elif line.teilnehmer_firma == 'Intern':
            print(f'Skipping {line.rownumber}: '
                  f'Firma intern but no link to Persons')
            continue
        else:
            # no teilnehmer_id so is external from a school or elsewhere
            first_name = line.teilnehmer_vorname
            last_name = line.teilnehmer_nachname

            if not all((email, first_name, last_name)):
                print(f'Skipping {line.rownumber}: '
                      'Subscription misses one of '
                      'email, firstname or lastname')
                continue

            external = maybe_external_in_ldap.setdefault(email, dict(
                id=uuid4(),
                first_name=first_name,
                last_name=last_name,
                organisation=line.teilnehmer_firma,
                subscriptions=[],
                email=email
            ))
            external['subscriptions'].append(dict(
                course_event_id=course_event.id,
                completed=completed
            ))

    assert not droppped_teilnehmer_ids
    assert not emails_by_teilnehmer_id

    return errors, persons, maybe_external_in_ldap


def map_persons_to_known_ldap_user(person_record, session):
    """
    Since the exported persons table contains records without email
    from various sources, we have to try to map it to an existing record
    or create a new one.

    The ldap fetched users have an attendee created with
    first_name, last_name and email set on the attendee as well.

    Returns an attendee or None
    """
    code = None
    if 'code' in person_record:
        code = person_record['code']
    email = person_record['email']

    if code:
        user = session.query(User).filter_by(source_id=code).first()
        if user:
            if email and user.username != email:
                # set email to most up-to-date
                email = user.username

            if not user.attendee:
                raise InconsistencyError(
                    f'{email} - {code}: user should have an attendee',
                    'Personen.txt',
                )
            return user.attendee
        print(f'LDAP CODE: {code} not found, Email {email} not searched')
    elif email:
        user = session.query(User).filter_by(username=email).first()
        if user:
            if not user.attendee:
                raise InconsistencyError(
                    f'{email}: user should have an attendee',
                    'Personen.txt',
                )
            return user.attendee
        print(f'LDAP EMAIL: {email} not found')

    else:
        identifier = person_record.get('obj_id') or email
        print(f'No identifier for user with OBJ_ID {identifier}')
    return None


def parse_ims_data(
        subscriptions_file,
        events_file,
        courses_file,
        persons_file,
):
    gathered_errors = {}

    # raw extraction
    raw_persons = parse_persons(persons_file)

    errors, courses = parse_courses(courses_file)

    if errors:
        gathered_errors['parse_courses'] = errors
        return gathered_errors, None, None, None, None, None

    errors, events = parse_events(events_file, courses)
    if errors:
        gathered_errors['parse_events'] = errors
        return gathered_errors, None, None, None, None, None

    errors, persons, possible_ldap_users = parse_subscriptions(
        subscriptions_file, raw_persons, events)

    if errors:
        gathered_errors['parse_subscriptions'] = errors

    return gathered_errors, persons, courses, events, possible_ldap_users


def import_ims_data(session, persons, courses, events, possible_ldap_users):

    print('-- Import IMS DATA to database with LDAP --')

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
            ReservationTemplate(**data),
            CancellationTemplate(**data),
            ReminderTemplate(**data)
        ))

    for obj_id, person in persons.items():
        attendee = map_persons_to_known_ldap_user(person, session)
        if not attendee:
            statistics['LDAP_not_found'] += 1
            continue
        statistics['LDAP_found'] += 1
        subscriptions = person['subscriptions']
        if not subscriptions:
            continue
        session.add_all((
            CourseReservation(
                attendee_id=attendee.id,
                course_event_id=r['course_event_id'],
                event_completed=r['event_completed']
            ) for r in subscriptions
        ))

    for record in possible_ldap_users.values():
        attendee = map_persons_to_known_ldap_user(record, session)
        if not attendee:
            statistics['external_not_found'] += 1
            continue
        statistics['external_found'] += 1
        session.add_all((
            CourseReservation(
                attendee_id=attendee.id,
                course_event_id=r['course_event_id']
            ) for r in record['subscriptions']
        ))
    return statistics
