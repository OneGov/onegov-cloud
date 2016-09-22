import codecs
import os
import textwrap

from datetime import datetime, timedelta
from onegov.core.utils import module_path
from onegov.event import EventCollection
from onegov.form import FormCollection
from onegov.libres import ResourceCollection
from onegov.page import PageCollection
from onegov.org.models import Organisation
from sedate import as_datetime


def create_new_organisation(app, name):

    org = Organisation(name=name)
    org.homepage_structure = textwrap.dedent("""
        <row>
            <column span="8">
                <homepage-cover />
                <news />
            </column>
            <column span="4">
                <panel>
                    <links title="Dienstleistungen">
                        <link url="./formulare"
                            description="Anfragen &amp; Rückmeldungen">
                            Formulare
                        </link>
                        <link url="./ressourcen"
                            description="Räume &amp; Tageskarten">
                            Reservationen
                        </link>
                    </links>
                </panel>
                <panel>
                    <events />
                </panel>
                <panel>
                    <links title="Verzeichnisse">
                        <link url="./personen"
                            description="Alle Kontakte">
                            Personen
                        </link>
                        <link url="./fotoalben"
                            description="Impressionen">
                            Fotoalben
                        </link>
                        <link url="./a-z"
                            description="Kataolg A-Z">
                            Themen
                        </link>
                    </links>
                </panel>
            </column>
        </row>
    """)

    session = app.session()
    session.add(org)

    add_root_pages(session)
    add_builtin_forms(session)
    add_events(session, name)
    add_resources(app.libres_context)

    return org


def add_root_pages(session):
    pages = PageCollection(session)

    pages.add_root(
        "Organisation",
        name='organisation',
        type='topic',
        meta={'trait': 'page'}
    )
    pages.add_root(
        "Themen",
        name='themen',
        type='topic',
        meta={'trait': 'page'}
    )
    pages.add_root(
        "Kontakt",
        name='kontakt',
        type='topic',
        meta={'trait': 'page'}
    )
    pages.add_root(
        "Aktuelles",
        name='aktuelles',
        type='news',
        meta={'trait': 'news'}
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
