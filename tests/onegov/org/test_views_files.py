from datetime import date
from datetime import datetime
from datetime import time
from morepath import Identity
from webtest import Upload
from sedate import standardize_date

from onegov.file import FileCollection
from onegov.org.models import GeneralFileCollection
from onegov.org.request import OrgRequest
from onegov.org.views.files import handle_publish
from onegov.org.views.files import handle_unpublish
from onegov.org.views.files import handle_update_publish_date
from onegov.org.views.files import toggle_publication
from onegov.org.views.files import view_file_details
from onegov.org.views.files import view_get_file_collection


def DummyRequest(app, method='GET', csrf=True):
    request = OrgRequest({
        'PATH_INFO': 'http://example.com',
        'SERVER_NAME': 'example.com',
        'SERVER_PORT': '80',
        'wsgi.url_scheme': 'http',
    }, app)
    request.identity = Identity(
        userid='foo',
        groupid='admins',
        role='admin',
        application_id=app.application_id
    )
    request.method = method
    if method == 'POST' and csrf:
        request.GET['csrf-token'] = request.new_csrf_token().decode('utf-8')
    return request


def test_view_get_file_collection(org_app):
    files = GeneralFileCollection(org_app.session())

    request = DummyRequest(org_app)
    result = view_get_file_collection(files, request)
    assert result['grouped'] == ()

    file = files.add('readme.txt', b'README')
    result = view_get_file_collection(files, request)
    files = result['grouped']
    assert len(files) == 1
    assert files[0][0] == 'R'
    assert len(files[0][1]) == 1
    assert files[0][1][0][1] == file.id
    assert files[0][1][0][2] == 'readme.txt'
    assert files[0][1][0][6] == 'text/plain'


def test_view_file_details(org_app):
    files = FileCollection(org_app.session())
    file = files.add('readme.txt', b'README')

    request = DummyRequest(org_app)
    html = view_file_details(file, request)
    # TODO: Check response headers
    assert f'http://example.com/storage/{file.id}' in html
    assert 'Öffentlich' in html
    assert 'Publikationsdatum:' not in html
    assert 'keine Publikation' in html

    file.published = False
    file.publication = True
    html = view_file_details(file, request)
    assert 'Privat' in html
    assert 'Publikationsdatum:' in html
    assert '<span>Publikation</span>' in html


def test_handle_publish(org_app):
    files = FileCollection(org_app.session())
    file = files.add('readme.txt', b'README')
    file.published = False
    assert file.published is False

    request = DummyRequest(org_app, 'POST')
    handle_publish(file, request)
    assert file.published is True

    file.published = False
    start = standardize_date(datetime.now(), 'Europe/Zurich')
    file.publish_date = start
    end = standardize_date(datetime.now(), 'Europe/Zurich')
    file.publish_end_date = end
    assert file.published is False
    assert file.publish_date == start
    assert file.publish_end_date == end

    handle_publish(file, request)
    assert file.published is True
    assert file.publish_date is None
    assert file.publish_end_date is None


def test_handle_unpublish(org_app):
    files = FileCollection(org_app.session())
    file = files.add('readme.txt', b'README')
    assert file.published is True

    request = DummyRequest(org_app, 'POST')
    handle_unpublish(file, request)
    assert file.published is False

    request = DummyRequest(org_app, 'POST')
    handle_unpublish(file, request)
    assert file.published is False


def test_toggle_publication(org_app):
    files = FileCollection(org_app.session())
    file = files.add('readme.txt', b'README')
    assert file.publication is False

    request = DummyRequest(org_app, 'POST')
    toggle_publication(file, request)
    assert file.publication is True

    toggle_publication(file, request)
    assert file.publication is False


def test_handle_update_publish_date(org_app):
    files = FileCollection(org_app.session())
    file = files.add('readme.txt', b'README')

    request = DummyRequest(org_app, 'POST')
    handle_update_publish_date(file, request)
    start = datetime.combine(date.today(), time(0, 0))
    start = standardize_date(start, 'Europe/Zurich')
    # TODO: Correct?
    assert file.publish_date == start
    assert file.publish_end_date is None

    file.publish_date = None
    request = DummyRequest(org_app, 'POST')
    request.POST['date'] = ''
    request.POST['hour'] = '11:00'
    handle_update_publish_date(file, request)
    start = datetime.combine(date.today(), time(11, 0))
    start = standardize_date(start, 'Europe/Zurich')
    assert file.publish_date == start
    assert file.publish_end_date is None

    request = DummyRequest(org_app, 'POST')
    request.POST['date'] = '2023-01-04'
    request.POST['hour'] = '16:00'
    handle_update_publish_date(file, request)
    start = datetime(2023, 1, 4, 16, 0)
    start = standardize_date(start, 'Europe/Zurich')
    assert file.publish_date == start
    assert file.publish_end_date is None

    request = DummyRequest(org_app, 'POST')
    request.POST['date'] = '2023-01-01'
    request.POST['hour'] = '00:00'
    request.POST['end-date'] = '2023-01-10'
    request.POST['end-hour'] = '12:00'
    handle_update_publish_date(file, request)
    start = datetime(2023, 1, 1, 0, 0)
    start = standardize_date(start, 'Europe/Zurich')
    assert file.publish_date == start
    end = datetime(2023, 1, 10, 12, 0)
    end = standardize_date(end, 'Europe/Zurich')
    assert file.publish_end_date == end

    request = DummyRequest(org_app, 'POST')
    request.POST['clear_start_date'] = '1'
    handle_update_publish_date(file, request)
    assert file.publish_date is None
    assert file.publish_end_date == end

    request = DummyRequest(org_app, 'POST')
    request.POST['clear_end_date'] = '1'
    handle_update_publish_date(file, request)
    assert file.publish_date is None
    assert file.publish_end_date is None


def test_view_files(client):
    assert client.get('/files', expect_errors=True).status_code == 403

    client.login_admin()

    files_page = client.get('/files')

    assert "Noch keine Dateien hochgeladen" in files_page

    files_page.form['file'] = Upload('Test.txt', b'File content.')
    files_page.form.submit()

    files_page = client.get('/files')
    assert "Noch keine Dateien hochgeladen" not in files_page
    assert 'Test.txt' in files_page
