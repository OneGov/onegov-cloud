from onegov.core.security import Private
from onegov.org.views.editor import get_form_class, handle_page_form
from onegov.town6 import TownApp
from onegov.org.models import Editor


@TownApp.form(model=Editor, template='form.pt', permission=Private,
              form=get_form_class)
def town_handle_page_form(self, request, form):
    return handle_page_form(self, request, form)
