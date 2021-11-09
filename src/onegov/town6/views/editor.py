from onegov.core.security import Private
from onegov.org.views.editor import get_form_class, handle_page_form, view_topics_sort
from onegov.town6 import TownApp
from onegov.org.models import Editor
from onegov.town6.layout import EditorLayout


@TownApp.form(model=Editor, template='form.pt', permission=Private,
              form=get_form_class)
def town_handle_page_form(self, request, form):
    return handle_page_form(
        self, request, form, EditorLayout(self, request, site_title=None)
    )


@TownApp.html(
    model=Editor,
    template='sort.pt',
    name='sort',
    permission=Private
)
def town_view_topics_sort(self, request):
    return view_topics_sort(self, request, EditorLayout(self, request, 'sort'))
