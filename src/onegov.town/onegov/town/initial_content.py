import mistune
import textwrap

from datetime import datetime, timedelta
from onegov.core.utils import module_path
from onegov.event import EventCollection
from onegov.libres import ResourceCollection
from onegov.org.initial_content import (
    add_builtin_forms, builtin_form_definitions)
from onegov.org.models import Organisation
from onegov.page import PageCollection
from sedate import as_datetime


def create_new_organisation(app, name, reply_to=None, forms=None):
    session = app.session()

    # can only be called if no organisation is defined yet
    assert not session.query(Organisation).first()

    org = Organisation(name=name)
    org.reply_to = reply_to
    org.homepage_structure = textwrap.dedent("""\
        <row>
            <column span="8">
                <homepage-tiles />
                <news />
            </column>
            <column span="4">
                <panel>
                    <services />
                </panel>
                <panel>
                    <events />
                </panel>
                <panel>
                    <directories />
                </panel>
            </column>
        </row>
    """)

    session.add(org)

    forms = forms or builtin_form_definitions(
        module_path('onegov.town', 'forms/builtin'))

    add_root_pages(session)
    add_builtin_forms(session, forms)
    add_resources(app.libres_context)
    add_events(session, name)
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
        Der Online Schalter für Ihre Gemeinde kann ab sofort genutzt
        werden. Um erste Schritte, mehr Informationen und eine kurze Übersicht
        zu erhalten klicken Sie einfach auf den Titel dieser Nachricht.
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
