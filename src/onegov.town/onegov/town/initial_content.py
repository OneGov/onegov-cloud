from datetime import datetime, timedelta
from onegov.core.utils import module_path
from onegov.event import EventCollection
from onegov.reservation import ResourceCollection
from onegov.org.initial_content import add_builtin_forms
from onegov.org.initial_content import builtin_form_definitions
from onegov.org.initial_content import add_filesets, add_pages, load_content
from onegov.org.models import Organisation
from sedate import as_datetime


def create_new_organisation(app, name, reply_to=None, forms=None,
                            create_files=True, path=None):
    session = app.session()

    path = path or module_path('onegov.town', 'content/de.yaml')
    content = load_content(path)

    # can only be called if no organisation is defined yet
    assert not session.query(Organisation).first()

    org = Organisation(name=name, **content['organisation'])
    org.reply_to = reply_to
    session.add(org)

    forms = forms or builtin_form_definitions(
        module_path('onegov.town', 'forms/builtin'))

    add_pages(session, path)
    add_builtin_forms(session, forms)
    add_resources(app.libres_context)
    add_events(session, name)

    if create_files:
        add_filesets(
            session, name, module_path('onegov.town', 'content/de.yaml'))

    session.flush()


def add_resources(libres_context):
    resource = ResourceCollection(libres_context)
    resource.add(
        "SBB-Tageskarte",
        'Europe/Zurich',
        type='daypass',
        name='sbb-tageskarte'
    )


def add_events(session, org_name):
    start = as_datetime(datetime.today().date())
    while start.weekday() != 6:
        start = start + timedelta(days=1)

    events = EventCollection(session)
    event = events.add(
        title="150 Jahre {}".format(org_name),
        start=start + timedelta(hours=11, minutes=0),
        end=start + timedelta(hours=22, minutes=0),
        timezone="Europe/Zurich",
        tags=["Party"],
        location="Sportanlage",
        content={
            "description": "Lorem ipsum.",
            "organizer": "Gemeindeverwaltung"
        },
        meta={"submitter_email": "info@example.org"},
    )
    event.submit()
    event.publish()
    event = events.add(
        title="Gemeindeversammlung",
        start=start + timedelta(days=2, hours=20, minutes=0),
        end=start + timedelta(days=2, hours=22, minutes=30),
        timezone="Europe/Zurich",
        tags=["Politics"],
        location="Gemeindesaal",
        content={
            "description": "Lorem ipsum.",
            "organizer": "Gemeindeverwaltung"
        },
        meta={"submitter_email": "info@example.org"},
    )
    event.submit()
    event.publish()
    event = events.add(
        title="MuKi Turnen",
        start=start + timedelta(days=2, hours=10, minutes=0),
        end=start + timedelta(days=2, hours=11, minutes=0),
        recurrence=(
            "RRULE:FREQ=WEEKLY;WKST=MO;BYDAY=TU,TH;UNTIL={0}".format(
                (start + timedelta(days=31)).strftime('%Y%m%dT%H%M%SZ')
            )
        ),
        timezone="Europe/Zurich",
        tags=["Sports"],
        location="Turnhalle",
        content={
            "description": "Lorem ipsum.",
            "organizer": "Frauenverein"
        },
        meta={"submitter_email": "info@example.org"},
    )
    event.submit()
    event.publish()
    event = events.add(
        title="Grümpelturnier",
        start=start + timedelta(days=7, hours=10, minutes=0),
        end=start + timedelta(days=7, hours=18, minutes=0),
        timezone="Europe/Zurich",
        tags=["Sports"],
        location="Sportanlage",
        content={
            "description": "Lorem ipsum.",
            "organizer": "Sportverein"
        },
        meta={"submitter_email": "info@example.org"},
    )
    event.submit()
    event.publish()
