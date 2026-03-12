from __future__ import annotations

import textwrap

from onegov.core.utils import module_path
from onegov.form import FormCollection
from onegov.org.initial_content import add_filesets, load_content, add_pages
from onegov.org.models import Organisation


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.feriennet.app import FeriennetApp


def create_new_organisation(
    app: FeriennetApp,
    name: str,
    create_files: bool = True,
    path: str | None = None,
    locale: str = 'de_CH'
) -> Organisation:

    locales = {
        'de_CH': 'content/de.yaml',
        'fr_CH': 'content/fr.yaml',
        'it_CH': 'content/it.yaml',
    }

    path = path or module_path('onegov.feriennet', locales[locale])
    content = load_content(path)

    org = Organisation(name=name, **content['organisation'])
    org.meta['locales'] = locale

    session = app.session()
    session.add(org)

    add_pages(session, path)

    forms = FormCollection(session).definitions

    if locale == 'de_CH':
        forms.add(
            name='kontakt',
            title='Kontakt',
            meta={
                'lead': (
                    'Haben Sie Fragen oder eine Anregung? '
                    'Rufen Sie uns einfach an oder benutzen Sie dieses '
                    'Formular.'
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
    elif locale == 'fr_CH':
        forms.add(
            name='contact',
            title='Contact',
            meta={
                'lead': (
                    'Avez-vous des questions ou des commentaires ? '
                    'Appelez-nous simplement, ou utilisez le formulaire '
                    'suivant.'
                )
            },
            definition=textwrap.dedent("""\
                Prénom *= ___
                Nom *= ___
                Telefon *= ___
                Émail *= @@@
                Message *= ...[12]
            """),
            type='builtin'
        )
    elif locale == 'it_CH':
        forms.add(
            name='contatto',
            title='Contatto',
            meta={
                'lead': (
                    'Avete domande o suggerimenti? '
                    'Potete telefonarci o riempire questo formulario.'
                )
            },
            definition=textwrap.dedent("""\
                Nome *= ___
                Cognome *= ___
                Telefono *= ___
                E-mail *= @@@
                Comunicazione *= ...[12]
            """),
            type='builtin'
        )
    else:
        raise NotImplementedError

    if create_files:
        add_filesets(
            session, name, module_path('onegov.feriennet', locales[locale])
        )

    return org
