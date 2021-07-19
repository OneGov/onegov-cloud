from onegov.core.security import Private
from onegov.editorjs.fields import EditorJsField
from onegov.form import Form
from onegov.org.forms.fields import HtmlField
from onegov.org.models import Organisation
from onegov.town6 import TownApp
from onegov.town6.layout import DefaultLayout


class EditorJSForm(Form):

    editor_js_test = EditorJsField(
        label='Text'
    )

    text_html = HtmlField(
        label='Text Formcode'
    )


@TownApp.form(
    model=Organisation,
    permission=Private,
    template='form.pt',
    form=EditorJSForm,
    name='editorjs'
)
def view_playground(self, request, form):
    layout = DefaultLayout(self, request)
    layout.include_editor()

    if form.submitted(request):
        form.populate_obj(obj=self)
        print(self.editor_js_test.blocks)

    else:
        form.process(obj=self)

    return {
        'title': 'Playground',
        'layout': DefaultLayout(self, request),
        'form': form
    }
