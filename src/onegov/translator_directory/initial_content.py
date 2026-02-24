from __future__ import annotations

from onegov.core.utils import module_path
from onegov.org.initial_content import load_content, add_pages
from onegov.org.models import Organisation


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.translator_directory.app import TranslatorDirectoryApp


def create_new_organisation(
    app: TranslatorDirectoryApp,
    name: str,
    locale: str = 'de_CH'
) -> Organisation:
    # Todo: add default languages
    assert locale == 'de_CH'

    path = module_path('onegov.translator_directory', 'content/de.yaml')
    content = load_content(path)

    org = Organisation(name=name, **content['organisation'])
    org.meta['locales'] = locale

    session = app.session()
    session.add(org)

    add_pages(session, path)

    return org
