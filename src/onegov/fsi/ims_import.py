"""
Files:

- Personen -> we have it from LDAP
- Teilnehmer: represents reservation table
- Ausführungen: the course events
- Kurse: courses, ignore everything you can also in the event

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
    courses = {}
    for line in csvfile.lines:
        name = line.kurzbeschreibung
        courses[line.vorgangsnr] = Course(
                id=uuid4(),
                name=name,
                description=name        # Where is the long description?
            )
    return courses


def parse_date(val):
    date_ = dateutil.parser.parse(val)
    return replace_timezone(date_, 'UTC')


def parse_status(val):
    mapping = {
        'Abgeschlossen': 'confirmed'
    }
    return mapping[val]


@with_open
def parse_events(csvfile, courses):
    events = {}
    for line in csvfile.lines:
        parent_course = courses[line.proc_id_kv]
        event = CourseEvent(
            id=uuid4(),
            course_id=parent_course.id,
            location=line.kurslokal,
            start=parse_date(line.kurs_von),
            end=parse_date(line.kurs_bis),
            presenter_name=line.referent_name,
            presenter_company=line.referent_firma,
            min_attendees=line.teilnehmer_min,
            max_attendees=line.teilnehmer_max,
            status=parse_status(line.status),
        )
        events[line.proc_id] = event
    return events


def parse_completed(val):
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


def import_ims_data(
        session,
        attendees_file,
        events_file,
        courses_file,
):

    courses = parse_courses(courses_file)
    events = parse_events(events_file, courses)
    errors, reservations = parse_reservations(attendees_file, session, events)

    if errors:
        return errors

    session.add_all(courses.values())
    session.add_all(events.values())
    session.add_all(reservations)
    session.flush()

    return []
