from morepath import redirect
from onegov.core.security import Public
from onegov.org.models import Organisation
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.user import Auth


@TranslatorDirectoryApp.view(model=Organisation, permission=Public)
def view_org(self, request, layout=None):
    """ Renders the homepage. """

    if not request.is_logged_in:
        return redirect(request.class_link(Auth, name='login'))

    if request.is_translator:
        return redirect(request.class_link(TranslatorCollection, name='self'))

    return redirect(request.class_link(TranslatorCollection))
