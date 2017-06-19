import textwrap

from onegov.core.utils import module_path
from onegov.form import FormCollection
from onegov.org.initial_content import add_filesets, load_content, add_pages
from onegov.org.models import Organisation


def create_new_organisation(app, name, create_files=True, path=None):
    path = path or module_path('onegov.feriennet', 'content/de.yaml')
    content = load_content(path)

    org = Organisation(name=name, **content['organisation'])

    session = app.session()
    session.add(org)

    add_pages(session, path)

    forms = FormCollection(session).definitions
    forms.add(
        name='kontakt',
        title="Kontakt",
        meta={
            'lead': (
                "Haben Sie Fragen oder eine Anregung? "
                "Rufen Sie uns einfach an oder benutzen Sie dieses Formular."
            )
        },
        definition=textwrap.dedent("""\
            Vorname *= ___
            Nachname *= ___
            Telefon *= ___
            E-Mail *= @@@
            Mitteilung *= ...[12]
        """),
        type='builtin'
    )

    if create_files:
        add_filesets(
            session, name, module_path('onegov.feriennet', 'content/de.yaml')
        )

    return org
