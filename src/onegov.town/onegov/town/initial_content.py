import codecs
import mistune
import os
import textwrap

from datetime import datetime, timedelta
from onegov.core.utils import module_path
from onegov.event import EventCollection
from onegov.form import FormCollection
from onegov.libres import LibresIntegration, ResourceCollection
from onegov.page import PageCollection
from onegov.town.models import Town
from sedate import as_datetime


def add_initial_content(libres_registry, session_manager, town_name,
                        form_definitions=None, reply_to=None):
    """ Adds the initial content for the given town on the given session.
    All content that comes with a new town is added here.

    Note, the ``form_definitions`` parameter is used to speed up testing,
    you usually do not want to specify it.

    """

    session = session_manager.session()

    libres_context = LibresIntegration.libres_context_from_session_manager(
        libres_registry, session_manager)

    # can only be called if no town is defined yet
    assert not session.query(Town).first()

    if reply_to:
        meta = {
            'reply_to': reply_to
        }
    else:
        meta = {}

    session.add(Town(name=town_name, meta=meta))

    add_root_pages(session)
    add_builtin_forms(session, form_definitions)
    add_resources(libres_context)
    add_events(session, town_name)
    add_welcome_page(session)

    session.flush()


def add_root_pages(session):
    pages = PageCollection(session)

    pages.add_root(
        "Leben & Wohnen",
        name='leben-wohnen',
        type='topic',
        meta={'trait': 'page'}
    ),
    pages.add_root(
        "Kultur & Freizeit",
        name='kultur-freizeit',
        type='topic',
        meta={'trait': 'page'}
    ),
    pages.add_root(
        "Bildung & Gesellschaft",
        name='bildung-gesellschaft',
        type='topic',
        meta={'trait': 'page'}
    ),
    pages.add_root(
        "Gewerbe & Tourismus",
        name='gewerbe-tourismus',
        type='topic',
        meta={'trait': 'page'}
    ),
    pages.add_root(
        "Politik & Verwaltung",
        name='politik-verwaltung',
        type='topic',
        meta={'trait': 'page'}
    )
    pages.add_root(
        "Aktuelles",
        name='aktuelles',
        type='news',
        meta={'trait': 'news'}
    )


def add_welcome_page(session):

    # for now only in German, translating through gettext is not the right way
    # here, because it splits the text into fragments which results in an
    # incoherent text
    title = "Willkommen bei OneGov"

    lead = """
        Ihre neuer Online Schalter für Gemeinde kann ab sofort genutzt werden.
        Um erste Schritte, mehr Informationen und eine kurze Übersicht zu
        erhalten klicken Sie einfach auf den Titel dieser Nachricht.
    """.replace('\n', '').strip('').replace('  ', ' ')

    text = textwrap.dedent("""\
        ## Erste Schritte

        Die folgenden Vorschläge helfen Ihnen sich in der OneGov Cloud zurecht
        zu finden. Falls Sie das lieber auf eigene Faust tun, können Sie diese
        Schritte gerne überspringen.

        **Melden Sie sich an**

        Sie können sich ab sofort mit Ihrer E-Mail Adresse anmelden. Sie haben
        das Passwort vergessen? Kein Problem,
        [setzen Sie es zurück](/request-password).

        **Passen Sie das Aussehen Ihren Bedürfnissen an**

        OneGov Cloud lässt sich nach Ihrem Gusto einrichten. Sie können das
        Logo, die Bilder auf der Startseite und mehr in den
        [Einstellungen](/einstellungen) ändern.

        **Stellen Sie Ihre Gemeinde vor**

        Klicken Sie auf **Leben & Wohnen** in der Navigation und
        anschliessend auf **Hinzufügen > Thema** gleich unterhalb der
        Hauptnavigation. Sie sehen **Hinzufügen** nicht? Dann müssen Sie sich
        erst noch anmelden.

        **Füllen Sie ein Formular aus**

        Im [Online-Schalter](/formulare) gibt es eine ganze Reihe von
        Formularen die Bürger ausfüllen können. Füllen Sie ein Formular aus
        und ein Ticket wird geöffnet.

        In den [Tickets](/tickets/ALL/open?page=0) können Sie das Ticket
        anschliessend bearbeiten. Übrigens: Sie können jederzeit eigene
        Formulare hinzufügen. Die mitgelieferten Formulare sind lediglich
        Vorschläge.

        ## Über Ihre OneGov Cloud Instanz

        Es gibt noch viel mehr zu entdecken - wir möchten an dieser Stelle
        nicht schon alles verraten.

        Ihre OneGov Cloud Instanz läuft auf einer Testumgebung, welche
        frühestens nach zwei Wochen verfällt. Sie können OneGov Cloud also
        in aller Ruhe testen.

        Zwar ist die Cloud für alle Personen zugänglich, wir stellen aber
        sicher dass sie nicht von Suchmaschinen gefunden wird. Wir
        möchten ja nicht das Ihre Bürger auf der falschen Seite landen.

        Sollten Sie Fragen haben, können Sie sich jederzeit an uns wenden:

        OneGov Cloud <br>
        Fabian Reinhard <br>
        Unter der Egg 5 <br>
        6004 Luzern <br>
        Tel. +41 41 511 22 50 <br>
        [fabian.reinhard@seantis.ch](fabian.reinhard@seantis.ch)

        ## Wie weiter

        Falls wir Sie überzeugen können melden Sie sich bei uns und wir
        können Ihre Testumgebung in eine produktive Umgebung überführen. Wir
        würden uns sehr freuen!
    """)

    pages = PageCollection(session)
    pages.add(
        parent=pages.by_path('aktuelles'),
        title=title,
        type='news',
        meta={
            'trait': 'page'
        },
        content={
            'lead': lead,
            'text': mistune.markdown(text, escape=False)
        }
    )


def add_builtin_forms(session, definitions=None):
    forms = FormCollection(session).definitions
    definitions = definitions or builtin_form_definitions()

    for name, title, definition in definitions:
        form = forms.by_name(name)

        if form:
            # update
            if form.title != title:
                form.title = title
            if form.definition != definition:
                form.definition = definition
        else:
            # add
            form = forms.add(
                name=name,
                title=title,
                definition=definition,
                type='builtin'
            )

        assert form.form_class().has_required_email_field, (
            "Each form must have at least one required email field"
        )


def builtin_form_definitions(path=None):
    """ Yields the name, title and the form definition of all form definitions
    in the given or the default path.

    """
    path = path or module_path('onegov.town', 'forms')

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
        "SBB-Tageskarte",
        'Europe/Zurich',
        type='daypass',
        name='sbb-tageskarte'
    )


def add_events(session, town_name):
    start = as_datetime(datetime.today().date())
    while start.weekday() != 6:
        start = start + timedelta(days=1)

    events = EventCollection(session)
    event = events.add(
        title="150 Jahre {}".format(town_name),
        start=start + timedelta(hours=11, minutes=0),
        end=start + timedelta(hours=22, minutes=0),
        timezone="Europe/Zurich",
        tags=["Party"],
        location="Sportanlage",
        content={"description": "Lorem ipsum."},
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
        content={"description": "Lorem ipsum."},
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
        content={"description": "Lorem ipsum."},
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
        content={"description": "Lorem ipsum."},
        meta={"submitter_email": "info@example.org"},
    )
    event.submit()
    event.publish()
