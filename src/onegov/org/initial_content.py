from __future__ import annotations

import codecs
import os
import yaml

from datetime import datetime, timedelta
from functools import lru_cache
from onegov.core.utils import module_path
from onegov.event import EventCollection
from onegov.file import FileSetCollection, FileCollection
from onegov.form import FormCollection
from onegov.org import _
from onegov.org.models import Organisation
from onegov.page import PageCollection
from onegov.reservation import ResourceCollection
from pathlib import Path
from sedate import as_datetime


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrPath
    from collections.abc import Callable, Iterable, Iterator
    from libres.context.core import Context as LibresContext
    from onegov.org.app import OrgApp
    from sqlalchemy.orm import Session
    from translationstring import TranslationString


@lru_cache(maxsize=1)
def load_content(path: str) -> dict[str, Any]:
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def absolute_path(path: str, base: StrPath) -> str:
    if path.startswith('/'):
        return path
    if path.startswith('~'):
        return os.path.expanduser(path)

    return os.path.join(base, path)


def create_new_organisation(
    app: OrgApp,
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

    path = path or module_path('onegov.org', locales[locale])
    content = load_content(path)

    org = Organisation(name=name, **content['organisation'])
    org.meta['locales'] = locale

    session = app.session()
    session.add(org)

    translator = app.translations.get(locale)
    assert translator is not None

    def translate(text: TranslationString) -> str:
        return text.interpolate(translator.gettext(text))

    add_pages(session, path)
    add_builtin_forms(session, locale=locale)
    add_events(session, name, translate, create_files)
    add_resources(app.libres_context, translate)

    if create_files:
        add_filesets(session, name, path)

    return org


def add_pages(session: Session, path: str) -> None:
    pages = PageCollection(session)

    for ix, page in enumerate(load_content(path).get('pages', ())):
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


def add_builtin_forms(
    session: Session,
    definitions: Iterable[tuple[str, str, str]] | None = None,
    locale: str = 'de_CH'
) -> None:

    forms = FormCollection(session).definitions
    definitions = definitions or builtin_form_definitions(locale=locale)

    for name, title, definition in definitions:
        if not forms.by_name(name):
            form = forms.add(
                name=name,
                title=title,
                definition=definition,
                type='custom'
            )

        assert form.form_class().has_required_email_field, (
            'Each form must have at least one required email field'
        )


def builtin_form_definitions(
    path: StrPath | None = None,
    locale: str = 'de_CH'
) -> Iterator[tuple[str, str, str]]:
    """ Yields the name, title and the form definition of all form definitions
    in the given or the default path.

    """
    locales = {
        'de_CH': 'forms/builtin/de',
        'fr_CH': 'forms/builtin/fr',
        'it_CH': 'forms/builtin/it',
    }

    path = path or module_path('onegov.org', locales[locale])

    for filename in os.listdir(path):
        if filename.endswith('.form'):
            name = filename.replace('.form', '')
            title, definition = load_definition(os.path.join(path, filename))
            yield name, title, definition


def load_definition(path: str) -> tuple[str, str]:
    """ Loads the title and the form definition from the given file. """

    with codecs.open(path, 'r', encoding='utf-8') as formfile:
        formlines = formfile.readlines()

        title = formlines[0].strip()
        definition = ''.join(formlines[3:])

        return title, definition


def add_resources(
    libres_context: LibresContext,
    translate: Callable[[TranslationString], str]
) -> None:

    resource = ResourceCollection(libres_context)
    resource.add(
        translate(_('Daypass')),
        'Europe/Zurich',
        type='daypass',
        name='tageskarte'
    )
    resource.add(
        translate(_('Conference room')),
        'Europe/Zurich',
        type='room',
        name='konferenzraum'
    )


def add_filesets(
    session: Session,
    organisation_name: str,
    path: str
) -> None:

    base = os.path.dirname(path)

    for fileset in load_content(path).get('filesets', ()):

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


def add_events(
    session: Session,
    name: str,
    translate: Callable[[TranslationString], str],
    create_files: bool
) -> None:

    start = as_datetime(datetime.today().date())

    while start.weekday() != 6:
        start = start + timedelta(days=1)

    imgs = Path(module_path('onegov.org', 'content/images'))

    events = EventCollection(session)
    event = events.add(
        title=translate(_('150 years {organisation}')).format(
            organisation=name
        ),
        start=start + timedelta(hours=11, minutes=0),
        end=start + timedelta(hours=22, minutes=0),
        timezone='Europe/Zurich',
        tags=['Party'],
        location=translate(_('Sports facility')),
        content={
            'description': translate(_('We celebrate our 150th anniversary.')),
            'organizer': name
        },
        meta={'submitter_email': 'info@example.org'}
    )

    if create_files:
        with (imgs / '3krgixyesbg-gregoire-bertaud.jpg').open('rb') as f:
            event.set_image(f)

    event.submit()
    event.publish()
    event = events.add(
        title=translate(_('General Assembly')),
        start=start + timedelta(days=2, hours=20, minutes=0),
        end=start + timedelta(days=2, hours=22, minutes=30),
        timezone='Europe/Zurich',
        tags=['Politics'],
        location=translate(_('Communal hall')),
        content={
            'description': translate(_('As every year.')),
            'organizer': name
        },
        meta={'submitter_email': 'info@example.org'},
    )

    if create_files:
        with (imgs / '3avlwp-7bg8-mikael-kristenson.jpg').open('rb') as f:
            event.set_image(f)

    event.submit()
    event.publish()
    event = events.add(
        title=translate(_('Community Gymnastics')),
        start=start + timedelta(days=2, hours=10, minutes=0),
        end=start + timedelta(days=2, hours=11, minutes=0),
        recurrence=(
            'RRULE:FREQ=WEEKLY;WKST=MO;BYDAY=TU,TH;UNTIL={}'.format(
                (start + timedelta(days=31)).strftime('%Y%m%dT%H%M%SZ')
            )
        ),
        timezone='Europe/Zurich',
        tags=['Sports'],
        location=translate(_('Gymnasium')),
        content={
            'description': translate(_('Get fit together.')),
            'organizer': translate(_("Women's Club"))
        },
        meta={'submitter_email': 'info@example.org'},
    )

    if create_files:
        with (imgs / 'uvdrvtwvqlu-swaminathan-jayaraman.jpg').open('rb') as f:
            event.set_image(f)

    event.submit()
    event.publish()
    event = events.add(
        title=translate(_('Football Tournament')),
        start=start + timedelta(days=7, hours=10, minutes=0),
        end=start + timedelta(days=7, hours=18, minutes=0),
        timezone='Europe/Zurich',
        tags=['Sports'],
        location=translate(_('Sports facility')),
        content={
            'description': translate(_('Amateurs welcome!')),
            'organizer': translate(_('Sports Association'))
        },
        meta={'submitter_email': 'info@example.org'},
    )

    if create_files:
        with (imgs / 'eg4dcqkdoka-nathan-rogers.jpg').open('rb') as f:
            event.set_image(f)

    event.submit()
    event.publish()
