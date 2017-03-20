import codecs
import os
import yaml

from datetime import datetime, timedelta
from functools import lru_cache
from onegov.core.utils import module_path
from onegov.event import EventCollection
from onegov.file import FileSetCollection, FileCollection
from onegov.form import FormCollection
from onegov.org.models import Organisation
from onegov.page import PageCollection
from onegov.reservation import ResourceCollection
from sedate import as_datetime


@lru_cache(maxsize=1)
def load_content(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.load(f)


def absolute_path(path, base):
    if path.startswith('/'):
        return path
    if path.startswith('~'):
        return os.path.expanduser(path)

    return os.path.join(base, path)


def create_new_organisation(app, name, create_files=True, path=None):
    path = path or module_path('onegov.org', 'content/de.yaml')
    content = load_content(path)

    org = Organisation(name=name, **content['organisation'])

    session = app.session()
    session.add(org)

    add_pages(session, path)
    add_builtin_forms(session)
    add_events(session, name)
    add_resources(app.libres_context)

    if create_files:
        add_filesets(session, name, path)

    return org


def add_pages(session, path):
    pages = PageCollection(session)

    for ix, page in enumerate(load_content(path).get('pages')):
        if 'parent' in page:
            parent = pages.by_path(page['parent'])
        else:
            parent = None

        pages.add(
            parent=parent,
            title=page['title'],
            type=page['type'],
            name=page.get('name', None),
            meta=page.get('meta', None),
            content=page.get('content', None),
            order=ix
        )


def add_builtin_forms(session, definitions=None):
    forms = FormCollection(session).definitions
    definitions = definitions or builtin_form_definitions()

    for name, title, definition in definitions:
        if not forms.by_name(name):
            form = forms.add(
                name=name,
                title=title,
                definition=definition,
                type='custom'
            )

        assert form.form_class().has_required_email_field, (
            "Each form must have at least one required email field"
        )


def builtin_form_definitions(path=None):
    """ Yields the name, title and the form definition of all form definitions
    in the given or the default path.

    """
    path = path or module_path('onegov.org', 'forms/builtin')

    for filename in os.listdir(path):
        if filename.endswith('.form'):
            name = filename.replace('.form', '')
            title, definition = load_definition(os.path.join(path, filename))
            yield name, title, definition


def load_definition(path):
    """ Loads the title and the form definition from the given file. """

    with codecs.open(path, 'r', encoding='utf-8') as formfile:
        formlines = formfile.readlines()

        title = formlines[0].strip()
        definition = ''.join(formlines[3:])

        return title, definition


def add_resources(libres_context):
    resource = ResourceCollection(libres_context)
    resource.add(
        "Tageskarte",
        'Europe/Zurich',
        type='daypass',
        name='tageskarte'
    )
    resource.add(
        "Konferenzraum",
        'Europe/Zurich',
        type='room',
        name='konferenzraum'
    )


def add_filesets(session, organisation_name, path):
    base = os.path.dirname(path)

    for fileset in load_content(path).get('filesets', tuple()):

        fs = FileSetCollection(session, fileset['type']).add(
            title=fileset['title'],
            meta=fileset.get('meta', None),
            content=fileset.get('content', None)
        )

        files = FileCollection(session, fileset['type'])

        for file in fileset.get('files'):
            filepath = absolute_path(file['path'], base)

            with open(filepath, 'rb') as f:

                fs.files.append(
                    files.add(
                        filename=os.path.basename(file['path']),
                        content=f,
                        note=file.get('note', '').format(
                            organisation=organisation_name
                        )
                    )
                )


def add_events(session, name):
    start = as_datetime(datetime.today().date())

    while start.weekday() != 6:
        start = start + timedelta(days=1)

    events = EventCollection(session)
    event = events.add(
        title="150 Jahre {}".format(name),
        start=start + timedelta(hours=11, minutes=0),
        end=start + timedelta(hours=22, minutes=0),
        timezone="Europe/Zurich",
        tags=["Party"],
        location="Sportanlage",
        content={
            "description": "Wir feiern das 150 jährige Bestehen.",
            "organizer": name
        },
        meta={"submitter_email": "info@example.org"},
    )
    event.submit()
    event.publish()
    event = events.add(
        title="Generalversammlung",
        start=start + timedelta(days=2, hours=20, minutes=0),
        end=start + timedelta(days=2, hours=22, minutes=30),
        timezone="Europe/Zurich",
        tags=["Politics"],
        location="Gemeindesaal",
        content={
            "description": "Alle Jahre wieder.",
            "organizer": name
        },
        meta={"submitter_email": "info@example.org"},
    )
    event.submit()
    event.publish()
    event = events.add(
        title="Gemeinsames Turnen",
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
            "description": "Gemeinsam fit werden.",
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
            "description": "Bolzen auf dem Platz.",
            "organizer": "Sportverein"
        },
        meta={"submitter_email": "info@example.org"},
    )
    event.submit()
    event.publish()
