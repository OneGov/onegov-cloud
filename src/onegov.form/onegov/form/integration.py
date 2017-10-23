from more.webassets import WebassetsApp
from onegov.core.security import Public
from onegov.form import _
from onegov.form.parser.snippets import Snippets


class FormApp(WebassetsApp):
    pass


@FormApp.path(path='formcode-snippets', model=Snippets)
def get_formcode_snippets():
    return Snippets()


@FormApp.json(model=Snippets, permission=Public)
def view_formcode_snippets(self, request):
    return {
        'labels': {
            'required': request.translate(_("Required")),
            'optional': request.translate(_("Optional")),
        },
        'snippets': tuple(self.translated(request))
    }


@FormApp.webasset_path()
def get_js_path():
    return 'assets/js'


@FormApp.webasset('formcode')
def get_formcode_asset():
    yield 'togglebutton.jsx'
    yield 'snippets.jsx'
