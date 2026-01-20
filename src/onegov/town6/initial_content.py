from __future__ import annotations

from onegov.core.utils import module_path
from onegov.reservation import ResourceCollection
from onegov.org.initial_content import add_builtin_forms
from onegov.org.initial_content import builtin_form_definitions
from onegov.org.initial_content import add_filesets, add_pages, load_content
from onegov.org.initial_content import add_events
from onegov.org.models import Organisation


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from libres.context.core import Context as LibresContext
    from onegov.core.framework import Framework
    from translationstring import TranslationString


def create_new_organisation(
    app: Framework,
    name: str,
    reply_to: str | None = None,
    forms: Iterable[tuple[str, str, str]] | None = None,
    create_files: bool = True,
    path: str | None = None,
    locale: str = 'de_CH'
) -> Organisation:

    session = app.session()

    locales = {
        'de_CH': 'content/de.yaml',
        'fr_CH': 'content/fr.yaml',
        'it_CH': 'content/it.yaml',
    }

    path = path or module_path('onegov.town6', locales[locale])
    content = load_content(path)

    # can only be called if no organisation is defined yet
    assert not session.query(Organisation).first()

    org = Organisation(name=name, **content['organisation'])
    org.reply_to = reply_to
    org.meta['locales'] = locale
    org.meta['e_move_url'] = 'https://www.eumzug.swiss/eumzug/#/global'
    session.add(org)

    form_locales = {
        'de_CH': 'forms/builtin/de',
        'fr_CH': 'forms/builtin/fr',
        'it_CH': 'forms/builtin/it',
    }

    forms = forms or builtin_form_definitions(
        module_path('onegov.town6', form_locales[locale]))

    translator = app.translations.get(locale)

    def translate(text: TranslationString) -> str:
        assert translator is not None
        return text.interpolate(translator.gettext(text))

    add_pages(session, path)
    add_builtin_forms(session, forms)
    # FIXME: Framework & LibresIntegration would be more accurate
    assert hasattr(app, 'libres_context')
    add_resources(app.libres_context)
    add_events(session, name, translate, create_files)

    if create_files:
        add_filesets(session, name, path)

    session.flush()
    return org


def add_resources(libres_context: LibresContext) -> None:
    resource = ResourceCollection(libres_context)
    resource.add(
        'SBB-Tageskarte',
        'Europe/Zurich',
        type='daypass',
        name='sbb-tageskarte'
    )
