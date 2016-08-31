from onegov.form import FormCollection
from onegov.page import PageCollection
from onegov.org.models import Organisation


def create_new_organisation(request, app, name):
    session = app.session()
    session.add(Organisation(name=name))

    pages = PageCollection(session)

    pages.add_root(
        title="Angebote",
        name='angebote',
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
        title="Über uns",
        name='ueber-uns',
        type='topic',
        meta={'trait': 'page'}
    )
    pages.add_root(
        title="Sponsoren",
        name='sponsoren',
        type='topic',
        meta={'trait': 'page'}
    )

    forms = FormCollection(session).definitions
    forms.add(
        name='kontakt',
        title="Kontakt",
        definition="""
            Vorname *= ___
            Nachname *= ___
            Telefon *= ___
            E-Mail *= @@@
            Mitteilung *= ...[12]
        """,
        type='builtin'
    )
