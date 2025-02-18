from __future__ import annotations

from morepath import redirect
from onegov.core.security import Public
from onegov.org.models import Organisation
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.translator import (
    TranslatorCollection)
from onegov.user import Auth


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.translator_directory.request import TranslatorAppRequest
    from webob import Response


@TranslatorDirectoryApp.view(model=Organisation, permission=Public)
def view_org(
    self: Organisation,
    request: TranslatorAppRequest
) -> Response:
    """ Renders the homepage. """

    if not request.is_logged_in:
        return redirect(request.class_link(Auth, name='login'))

    if (
        request.is_translator
        and (translator := request.current_user.translator)  # type:ignore
    ):
        return redirect(request.link(translator))

    return redirect(request.class_link(TranslatorCollection))
