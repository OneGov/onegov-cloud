import textwrap

from onegov.form import FormCollection
from onegov.org.models import Organisation
from onegov.page import PageCollection


def create_new_organisation(app, name):
    org = Organisation(name=name)
    org.homepage_cover = textwrap.dedent("""
        <p class="has-img">
            <img src="./static/images/balloons.jpg" />
        </p>
        <p>
            <a href="./angebote">Zu den Angeboten</a>
        </p>
    """.format(name=name))
    org.homepage_structure = textwrap.dedent("""\
        <row>
            <column span="8">
                <homepage-cover />
                <news />
            </column>
            <column span="4">
                <registration />

                <panel>
                    <links>
                        <link url="./personen"
                            description="Personen">
                            Team
                        </link>
                        <link url="./formular/kontakt"
                            description="Anfragen">
                            Kontakt
                        </link>
                        <link url="./aktuelles"
                            description="Neuigkeiten">
                            Aktuelles
                        </link>
                        <link url="./fotoalben"
                            description="Impressionen">
                            Fotoalben
                        </link>
                    </links>
                </panel>
            </column>
        </row>
    """)

    session = app.session()
    session.add(org)

    pages = PageCollection(session)

    pages.add_root(
        title="Organisation",
        name='organisation',
        type='topic',
        meta={'trait': 'page'}
    )
    pages.add_root(
        title="Teilnahmebedingungen",
        name='teilnahmebedingungen',
        type='topic',
        meta={'trait': 'page'}
    )
    pages.add_root(
        title="Sponsoren",
        name='sponsoren',
        type='topic',
        meta={'trait': 'page'}
    )
    pages.add_root(
        title="Aktuelles",
        name='aktuelles',
        type='news',
        meta={'trait': 'page'}
    )

    forms = FormCollection(session).definitions
    forms.add(
        name='kontakt',
        title="Kontakt",
        definition=textwrap.dedent("""\
            Vorname *= ___
            Nachname *= ___
            Telefon *= ___
            E-Mail *= @@@
            Mitteilung *= ...[12]
        """),
        type='builtin'
    )

    return org
