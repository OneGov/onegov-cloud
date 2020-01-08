"""
Files:

- Personen -> we have it from LDAP
- Teilnehmer: represents reservation table
- Ausführungen: the course events
- Kurse: courses, ignore everything you can also in the event

Some edge cases are to handle

- Missing start, end of a course event, they generally have BUCHUNGSTATUS = Keine Buchung
- Missing presenter names, can not be nullable in our case
- in Teilnehmer, ANWESEND can be missing

"""
from uuid import uuid4
import dateutil.parser
from sedate import replace_timezone

from onegov.core.csv import CSVFile
from onegov.fsi.models import CourseEvent, Course, CourseReservation, \
    CourseAttendee
from onegov.user import User


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


@with_open
def parse_courses(csvfile):
    errors = {}
    courses = {}
    for line in csvfile.lines:
        try:
            name = line.kurzbeschreibung
            courses[line.vorgangsnr] = Course(
                    id=uuid4(),
                    name=name,
                    description=name        # Where is the long description?
                )
        except Exception as e:
            errors[line.rownumber] = e.args[0]
            continue

    return errors, courses


def parse_date(val):
    if not val:
        raise TypeError('Emtpy value provided')
    date_ = dateutil.parser.parse(val)
    return replace_timezone(date_, 'UTC')


def parse_status(val):
    mapping = {
        'Abgeschlossen': 'confirmed',
        'Abgesagt': 'canceled',
        'Erfasst': 'created'
    }
    return mapping[val]


@with_open
def parse_events(csvfile, courses):
    events = {}
    errors = {}
    for line in csvfile.lines:

        # Block accepts empty end values, but fails if the start is not set
        parent_course = courses[line.proc_id_kv]
        date_lacking = not line.kurs_von or not line.kurs_bis
        if line.buchungsstatus == 'Keine Buchung' and date_lacking:
            print(f'Skipping line {line.rownumber}: '
                  f'course not done and lacking date')
            continue

        try:
            start = parse_date(line.kurs_von)
        except Exception as e:
            errors[line.rownumber] = e.args[0]
            continue
        try:
            end = parse_date(line.kurs_bis)
        except TypeError:
            end = start

        event = CourseEvent(
            id=uuid4(),
            course_id=parent_course.id,
            location=line.kurslokal,
            start=start,
            end=end,
            presenter_name=line.referent_name,
            presenter_company=line.referent_firma,
            min_attendees=line.teilnehmer_min,
            max_attendees=line.teilnehmer_max,
            status=parse_status(line.status),
        )
        events[line.proc_id] = event
    return errors, events


def parse_completed(val):
    if not val:
        raise TypeError('Empty Value in parse completed')
    return True if val == 'J' else False


@with_open
def parse_reservations(csvfile, session, events):
    reservations = []
    errors = {}

    for line in csvfile.lines:

        email = line.teilnehmer_email
        company = line.teilnehmer_firma

        if company == 'Intern':
            user = session.query(User).filter_by(username=email).first()
            if not user:
                errors[line.rownumber] = f'{email} not in user database'
                continue
            if not user.attendee:
                errors[line.rownumber] = f'{email} lacks its attendee'
                continue
            attendee = user.attendee
        else:
            attendee = session.query(CourseAttendee).filter_by(
                _email=email).first()
            if not attendee:
                errors[line.rownumber] = f'{email} not intern and not found'
                continue

        course_event = events.get(line.proc_id)
        if not course_event:
            errors[line.rownumber] = f'{line.proc_id} not in event file'
            continue

        res = CourseReservation(
            course_event_id=course_event.id,
            attendee_id=attendee.id,
            event_completed=parse_completed(line.anwesend)
        )
        reservations.append(res)
    return errors, reservations


@with_open
def parse_persons(csvfile, session):
    errors = {}
    persons = {}
    for line in csvfile.lines:
        obj_id = line.obj_id
        assert obj_id
        code = line.p_userid
        mail = line.p_email

        if not mail:
            errors[line.rownumber] = 'User with no email'
            continue

        # Find the user, if more than one exists, code is needed to compare
        persons.setdefault(obj_id, {
            'email': mail,
            'code': code,
            'company': line.teilnehmer_firma
        })
    return errors, persons


def import_ims_data(
        session,
        attendees_file,
        events_file,
        courses_file,
        persons_file,
        write_log=False
):
    gathered_errors = {}

    errors, persons = parse_persons(persons_file, session)
    assert False

    if errors:
        gathered_errors['parse_persons'] = errors

    errors, courses = parse_courses(courses_file)

    if errors:
        gathered_errors['parse_courses'] = errors
        return gathered_errors

    errors, events = parse_events(events_file, courses)
    if errors:
        gathered_errors['parse_events'] = errors
        return gathered_errors

    errors, reservations = parse_reservations(attendees_file, session, events)
    if errors:
        gathered_errors['parse_reservations'] = errors

    if gathered_errors:
        return gathered_errors

    session.add_all(courses.values())
    session.add_all(events.values())
    session.add_all(reservations)
    session.flush()

    return {}

