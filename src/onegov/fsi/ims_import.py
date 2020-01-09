"""
Dateien:

- Kurse: Die Liste der Kurse
- Personen -> importiert aus ldap
- Teilnehmer: repräsentiert die Anmeldungen mit referenz zu Personen/Ausführungen
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

Es werden nicht importiert:

- Personen, ohne Kürzel und Email sowie deren alte Anmeldungen
- Durchführungen mit BUCHUNGS_STATUS = Keine Buchung and Start/Ende fehlend
  werden auch nicht mehr importiert.
- Durchführungen ohne Start UND Ende unabhängig von Status

Vervollständigungen

- .local in email addressen wird herausgenommen
- Fehlender Wert für ANWESEND bei alten Anmeldungen wird mit JA gefüllt.
- Referent Kurs: Standard-Wert einfügen "Unbekannter Referent" sofern fehlend
- Fehlt die Email in Personen.txt wird noch in Teilnehmer.txt gesucht.

Als Externe Benutzer sollen erstellt werden:

Mit Beantwortung der Fragen zu klären, wie man solche in Personen.txt
  identifiziert.

"""
from collections import OrderedDict, defaultdict
from uuid import uuid4
import dateutil.parser
from sedate import replace_timezone

from onegov.core.csv import CSVFile
from onegov.fsi.models import CourseEvent, Course, CourseReservation, \
    CourseAttendee
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
    if not val:
        raise TypeError('Empty Value in parse completed')
    return True if val == 'J' else False


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
            'email': parse_email(line.p_email),
            'code': line.p_userid,
            # 'org': line.p_verwaltung,
            'first_name': line.p_vorname,
            'last_name': line.p_name,
            # 'valid_till': valid_till
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
            print(f'Skipping {line.rownumber}: parent course not found')
            continue

        date_lacking = not line.kurs_von or not line.kurs_bis
        if line.buchungsstatus == 'Keine Buchung' and date_lacking:
            print(f'Skipping line {line.rownumber}: '
                  f'status: Keine Buchung and lacking date')
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
        min_att = validate_integer(line.teilnehmer_min)
        max_att = validate_integer(line.teilnehmer_max)

        event = CourseEvent(
            id=uuid4(),
            course_id=parent_course.id,
            location=line.kurslokal,
            start=start,
            end=end,
            presenter_name=line.referent_name or default_name,
            presenter_company=line.referent_firma,
            min_attendees=min_att,
            max_attendees=max_att,
            status=parse_status(line.status),
        )
        events[line.proc_id] = event
    return errors, events


@with_open
def parse_subscriptions(csvfile, persons, events):
    print('-- parse_subscriptions --')

    reservations = []
    errors = OrderedDict()
    droppped_teilnehmer_ids = []
    external_attendees = []
    different_email_count = 0
    emails_choices_for_nonexisting = defaultdict(list)
    new_emails_for_existing = defaultdict(list)

    for line in csvfile.lines:
        teilnehmer_id = line.teilnehmer_id

        course_event_id = events.get(line.proc_id)
        if not course_event_id:
            print(f'Skipping {line.rownumber}: drop since no course event')
            continue

        email = parse_email(line.teilnehmer_email)

        if teilnehmer_id:
            person_obj = persons.get(line.teilnehmer_id)
            if not person_obj:
                print(
                    f'Skipping {line.rownumber}: '
                    f'dropping {line.teilnehmer_id} not in persons')
                continue

            # Fill missing Email or drop the user completely
            current_email = persons[teilnehmer_id]['email']
            code = persons[teilnehmer_id]['code']
            if not current_email:
                if email:
                    # print(f'-- {line.rownumber} person.email completed')
                    emails_choices_for_nonexisting[teilnehmer_id].append(email)
                    # persons[teilnehmer_id]['email'] = email
                elif not persons[teilnehmer_id]['code']:
                    print(f'Skipping {line.rownumber}: '
                          f'No email found at all, no code')
                    # del persons[teilnehmer_id]
                    droppped_teilnehmer_ids.append(teilnehmer_id)
                    continue
            else:
                # check if the email is different
                if current_email and not current_email == email:
                    # print(f'-- getting different email for {teilnehmer_id}')
                    identifier = f'{current_email}-{code}'
                    new_emails_for_existing[identifier].append(email)
                    different_email_count += 1
                    # print(f'person.email {current_email} v.s {email}')

            # first_name, last_name from two sources, Persons taking priority
            first_name = persons.get(teilnehmer_id, {}).get(
                'first_name') or line.teilnehmer_vorname

            last_name = persons.get(teilnehmer_id, {}).get(
                'last_name') or line.teilnehmer_nachname

        elif line.teilnehmer_firma == 'Intern':
            print(f'Skipping {line.rownumber}: '
                  f'Firma intern but no link to Persons')
            continue
        else:
            # no teilnehmer_id so is external from a school or elsewhere
            if not all((email, first_name, last_name)):
                print(f'Skipping {line.rownumber}: '
                      f'External person with no email, firstname or lastname')
                continue
            external_attendees.append(dict(
                first_name=first_name,
                last_name=last_name,
                email=email,
                organisation=line.teilnehmer_firma
            ))
    for key, val in new_emails_for_existing.items():
        print(f'-- Identifier {key} | Anmeldungen für ' + ', '.join(set(val)))

    for key, val in emails_choices_for_nonexisting:
        print(f' -- OBJ_ID {key}: Mögliche Addressen: ' + ', '.join(set(val)))

    # print(f'Different emails counted: {different_email_count}')
    return errors, reservations, droppped_teilnehmer_ids, external_attendees


def map_person_to_known_ldap_user(line, session):
    """
    Since the exported persons table contains records without email
    from various sources, we have to try to map it to an existing record
    or create a new one.

    The ldap fetched users have an attendee created with
    first_name, last_name and email set on the attendee as well.

    Returns an obj_id, attendee tuple
    """
    obj_id = line.obj_id
    assert obj_id
    org = line.p_verwaltung.strip()
    assert org

    code = line.p_userid.strip()        # compare with user.source_id
    email = line.p_email.strip()
    first_name = line.p_vorname.strip()
    last_name = line.p_name.strip()
    left_org = line.p_austrittsdatum.strip()
    valid_til = line.p_valid_till.strip()


    ldap_org = 'Kantonale Verwaltung Zug'

    # 1st stage: email and shortcode are right
    if code and email:
        user = session.query(User).filter_by(
            username=email, source_id=code).first()
        if user:
            if not user.attendee:
                raise InconsistencyError(
                    f'{email} - {code}: user should have an attendee',
                    'Personen.txt',
                    rownumber=line.rownumber
                )
            return obj_id, user.attendee
        else:
            # the person does not exists in ldap anymore
            raise InconsistencyError(
                f'{email} - {code}: no entry found in users',
                'Personen.txt',
                rownumber=line.rownumber
            )

    if email:
        user = session.query(User).filter_by(username=email).first()
        if user:
            assert user.attendee
            return user.attendee
        # else:
        #     # try to find the user/attendee as external one
        #     # does not make sense much, cause where from we have this data
        #     attendee = session.query(CourseAttendee).filter_by(
        #         _email=email).first()
        #     if attendee:
        #         return attendee
        #     else:
        #         raise InconsistencyError(
        #             f'{email}: no entry found in attendees (external)',
        #             'Personen.txt',
        #             rownumber=line.rownumber
        #         )
    # assuming this person was external
    was_external_for_sure = ldap_org != org


def find_lacking_person_email(persons, subscriptions):
    pass


def import_ims_data(
        session,
        subscriptions_file,
        events_file,
        courses_file,
        persons_file,
        write_log=False
):
    gathered_errors = {}

    # raw extraction
    persons = parse_persons(persons_file)

    errors, courses = parse_courses(courses_file)

    if errors:
        gathered_errors['parse_courses'] = errors
        return gathered_errors

    errors, events = parse_events(events_file, courses)
    if errors:
        gathered_errors['parse_events'] = errors
        return gathered_errors

    errors, subscriptions, dropped_person_ids, external = parse_subscriptions(
        subscriptions_file, persons, events)

    # Delete persons with no email at all and no code
    for person_id in dropped_person_ids:
        print(f'Dropping user with teilnehmer_id={person_id}')
        del persons[person_id]

    if errors:
        gathered_errors['parse_subscriptions'] = errors

    if gathered_errors:
        return gathered_errors

    # session.add_all(courses.values())
    # session.add_all(events.values())
    # session.add_all(subscriptions)
    # session.flush()

    return {}

