from conftest import create_org_app

from onegov.core.security import Secret
from onegov.org.app import OrgApp
from onegov.org.forms import ExportForm
from onegov.org.models import Export
from onegov.org.testing import Client


def test_export(request):

    class App(OrgApp):
        pass

    @App.export(
        id='my-export',
        form_class=ExportForm,
        permission=Secret,
        title="My Export",
        explanation="Foo bar.")
    class MyExport(Export):
        def run(self, form, session):
            return [[
                ('id', 'foo'),
                ('content', 'bar')
            ]]

    app = create_org_app(request, use_elasticsearch=False, cls=App)

    # the export should work for admins
    admin = Client(app)
    admin.login_admin()

    page = admin.get('/exporte')
    assert "My Export" in page
    assert "Foo bar." in page

    page = page.click("My Export")
    page.form['file_format'] = 'json'
    result = page.form.submit().json

    assert result == [
        {
            'id': 'foo',
            'content': 'bar'
        }
    ]

    # but because of our permission editors don't have a chance
    editor = Client(app)
    editor.login_editor()

    page = editor.get('/exporte')
    assert "My Export" not in page
    assert "Foo bar." not in page

    page = editor.get('/export/my-export', status=403)
    assert "Ihnen fehlt die nötige Berechtigung" in page
