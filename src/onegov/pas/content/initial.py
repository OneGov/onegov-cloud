from __future__ import annotations

from onegov.core.utils import module_path
from onegov.org.initial_content import load_content
from onegov.org.models import Organisation

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.core.framework import Framework


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

    locales = {'de_CH': 'content/de.yaml'}

    path = path or module_path('onegov.pas', locales[locale])
    content = load_content(path)

    # can only be called if no organisation is defined yet
    assert not session.query(Organisation).first()

    org = Organisation(name=name, **content['organisation'])
    org.reply_to = reply_to
    org.meta['locales'] = locale
    session.add(org)
    session.flush()

    return org
