import pytest
import requests
import transaction

from datetime import datetime, timedelta
from onegov.core.utils import module_path
from onegov.directory import DirectoryCollection
from onegov.file import FileCollection
from tests.shared.utils import create_image
from pytz import UTC
from sedate import utcnow
from tempfile import NamedTemporaryFile
from time import sleep


def test_browse_activities(browser):
    # admins
    browser.login_admin()
    browser.visit('/timeline')

    assert browser.is_text_present("Noch keine Aktivität")

    # anonymous
    browser.logout()
    browser.visit(
        '/timeline', expected_errors=[{'rgxp': '/timeline - Failed'}]
    )

    assert not browser.is_text_present("Noch keine Aktivität")


@pytest.mark.parametrize("field", (
    'Photo = *.png|*.jpg',
    'Photo *= *.png|*.jpg',
))
def test_browse_directory_uploads(browser, org_app, field):
    DirectoryCollection(org_app.session(), type='extended').add(
        title="Crime Scenes",
        structure="""
            Name *= ___
            Description *= ...
            {field}
        """.format(field=field),
        configuration="""
            title:
                - name
            order:
                - name
            display:
                content:
                    - name
                    - description
                    - photo
        """,
        type='extended'
    )

    transaction.commit()

    # create a new page with a picture
    photo = create_image(output=NamedTemporaryFile(suffix='.png'))

    browser.login_admin()
    browser.visit('/directories/crime-scenes/+new')
    browser.fill('name', "Seven Seas Motel")
    browser.fill('description', "First victim of Ice Truck Killer")
    browser.fill('photo', photo.name)
    browser.find_by_value("Absenden").click()

    assert browser.is_text_present("Seven Seas Motel")
    assert browser.is_element_present_by_css('.field-display img')

    src = browser.find_by_css('.field-display img')['src']

    # elect to keep the picture (default)
    browser.find_by_css('.edit-link').click()
    browser.fill('name', "Seven Seas Motel, Miami")
    browser.find_by_value("Absenden").click()

    assert browser.is_text_present("Seven Seas Motel, Miami")
    assert browser.is_element_present_by_css('.field-display img')
    assert browser.find_by_css('.field-display img')['src'] == src

    # elect to replace the picture
    photo = create_image(output=NamedTemporaryFile(suffix='.png'))

    browser.find_by_css('.edit-link').click()
    browser.choose('photo', 'replace')
    browser.find_by_name('photo')[3].value = photo.name
    browser.find_by_value("Absenden").click()

    assert browser.is_element_present_by_css('.field-display img')
    assert browser.find_by_css('.field-display img')['src'] != src

    # elect to delete the picture
    browser.find_by_css('.edit-link').click()
    browser.choose('photo', 'delete')
    browser.find_by_value("Absenden").click()

    if field.startswith('Photo ='):
        assert not browser.is_element_present_by_css('.field-display img')
    else:
        assert browser.is_text_present("Dieses Feld wird benötigt")


def test_upload_image_with_error(browser, org_app):
    DirectoryCollection(org_app.session(), type='extended').add(
        title="Crime Scenes",
        structure="""
            Name *= ___
            Description *= ...
            Photo = *.jpg|*.png
        """,
        configuration="""
            title:
                - name
            order:
                - name
            display:
                content:
                    - name
                    - description
                    - photo
        """,
        type='extended'
    )

    transaction.commit()

    # create a new page with a missing field (but do supply the picture)
    photo = create_image(output=NamedTemporaryFile(suffix='.png'))

    browser.login_admin()
    browser.visit('/directories/crime-scenes/+new')
    browser.fill('name', "Seven Seas Motel")
    browser.fill('photo', photo.name)
    browser.find_by_value("Absenden").click()

    assert browser.is_text_present("Dieses Feld wird benötigt")

    # try again with the missing field present
    browser.fill('description', "First victim of Ice Truck Killer")
    browser.find_by_value("Absenden").click()

    assert browser.is_text_present("Seven Seas Motel")

    # the image won't be there however (it gets cleared in between requests)
    assert not browser.is_element_present_by_css('.field-display img')


@pytest.mark.skip('Picture upload is needed to check scaling')
def test_directory_thumbnail_views(browser, org_app):

    DirectoryCollection(org_app.session(), type='extended').add(
        title="Jam Session",
        structure="""
            Name *= ___
            Photo = *.jpg|*.png
            Instruments = *.jpg|*.png
            """,
        configuration="""
            title:
                - name
            order:
                - name
            display:
                content:
                    - name
                    - instruments
                    - photo
            show_as_thumbnails:
                - photo
            """,
        type='extended'
    )

    transaction.commit()
    browser.login_admin()

    browser.visit('/directories/jam-session/+new')
    photo = create_image(output=NamedTemporaryFile(suffix='.png'))
    browser.fill('name', 'Bar59')
    browser.fill('photo', photo.name)
    browser.fill('instruments', photo.name)
    browser.find_by_value("Absenden").click()


@pytest.mark.skip("Passes locally, but not in CI, skip for now")
def test_browse_directory_editor(browser, org_app):
    browser.login_admin()
    browser.visit('/directories/+new')

    assert browser.is_element_present_by_css('.formcode-toolbar', wait_time=5)

    browser.fill('title', "Restaurants")

    # add a title through the dropdown menu
    browser.find_by_css('.formcode-toolbar-element').scroll_to()
    browser.find_by_css('.formcode-toolbar-element').click()

    browser.find_by_css('.formcode-snippet-name')[0].scroll_to()
    browser.find_by_css('.formcode-snippet-name')[0].click()

    # add a text through the dropdown menu
    browser.find_by_css('.formcode-toolbar-element').scroll_to()
    browser.find_by_css('.formcode-toolbar-element').click()
    sleep(.25)
    browser.find_by_css('.formcode-snippet-name')[1].scroll_to()
    browser.find_by_css('.formcode-snippet-name')[1].mouse_over()
    sleep(.25)
    browser.find_by_css('.formcode-snippet-required')[0].scroll_to()
    browser.find_by_css('.formcode-snippet-required')[0].click()

    assert browser.find_by_css('#structure').value == (
        "# Titel\n"
        "Text *= ___\n"
    )

    # Add the title to the title format
    browser.scroll_to_css('#title_format')
    assert browser.is_element_present_by_xpath(
        '(//div[@class="formcode-toolbar-element"])[2]', wait_time=5)

    browser.find_by_css('.formcode-toolbar-element')[1].click()
    browser.find_by_css('.formcode-snippet-name')[0].click()

    assert browser.find_by_css('#title_format').value == '[Titel/Text]'

    # Add it to the lead format as well
    browser.scroll_to_css('#lead_format')
    assert browser.is_element_present_by_xpath(
        '(//div[@class="formcode-toolbar-element"])[3]', wait_time=5)

    browser.find_by_css('.formcode-toolbar-element')[2].click()
    browser.find_by_css('.formcode-snippet-name')[0].click()

    assert browser.find_by_css('#lead_format').value == '[Titel/Text]'

    # Elect to show the fields in the main view
    browser.find_by_css('.formcode-select label').click()

    assert browser.find_by_css('#content_fields').value == "Titel/Text"

    # Save the form and ensure that after the load we get the same selections
    submit = browser.find_by_value("Absenden")
    submit.scroll_to()
    submit.click()

    browser.find_by_css('.edit-link').click()
    assert browser.find_by_css('.formcode-select input')[0].checked
    assert not browser.find_by_css('.formcode-select input')[1].checked


def test_browse_directory_coordinates(browser, org_app):
    DirectoryCollection(org_app.session(), type='extended').add(
        title="Restaurants",
        structure="""
            Name *= ___
            Tables = 0..1000
        """,
        configuration="""
            title: '[name]'
            lead: 'Offers [tables] tables'
            order:
                - name
            display:
                content:
                    - name
        """,
        meta={
            'enable_map': 'everywhere'
        },
        type='extended'
    )

    transaction.commit()

    # create two restaurants with two different coordinates
    browser.login_admin()
    browser.visit('/directories/restaurants/+new')
    browser.fill('name', "City Wok")
    browser.fill('tables', "10")
    assert browser.is_element_present_by_css('.add-point-active', wait_time=5)
    browser.execute_script('document.leafletmaps[0].panBy([-100, 100]);')
    browser.find_by_css('.add-point-active').click()
    browser.find_by_value("Absenden").click()

    browser.visit('/directories/restaurants/+new')
    browser.fill('name', "City Sushi")
    browser.fill('tables', "20")
    assert browser.is_element_present_by_css('.add-point-active', wait_time=5)
    browser.execute_script('document.leafletmaps[0].panBy([100, -100]);')
    browser.find_by_css('.add-point-active').click()
    browser.find_by_value("Absenden").click()

    # make sure the restaurants are visible in the overview
    browser.visit('/directories/restaurants')
    assert "Offers 20 tables" in browser.html
    assert "Offers 10 tables" in browser.html

    # as well as their points, which we can toggle
    assert not browser.is_element_present_by_css('.popup-title')
    assert not browser.is_element_present_by_css('.popup-lead')

    browser.find_by_css('.vector-marker')[1].click()
    assert browser.is_element_present_by_css('.popup-title')
    assert browser.is_element_present_by_css('.popup-lead')

    # the popup leads us to the restaurant
    browser.find_by_css('.popup-title').click()
    assert browser.is_element_present_by_id(
        'page-directories-restaurants-city-wok')


def test_publication_workflow(browser, temporary_path, org_app):
    path = temporary_path / 'foo.txt'

    with path.open('w') as f:
        f.write('bar')

    browser.login_admin()
    browser.visit('/files')

    # upload a file
    assert not browser.is_text_present("Soeben hochgeladen")
    browser.drop_file('.upload-dropzone', path)
    assert browser.is_text_present("Soeben hochgeladen")

    # show the details
    browser.find_by_css('.upload-filelist .untoggled').click()
    assert browser.is_text_present("Öffentlich")
    assert not browser.is_text_present("Privat")
    assert not browser.is_text_present("Publikationsdatum")

    # make sure the file can be downloaded
    file_url = browser.find_by_css('.file-preview')['href']
    r = requests.get(file_url)
    assert r.status_code == 200
    assert 'public' in r.headers['cache-control']

    # make sure unpublishing works
    browser.find_by_css('.publication .file-status-tag a').click()
    r = requests.get(file_url)
    assert r.status_code == 403

    assert browser.is_text_present("Privat", wait_time=1)
    assert browser.is_text_present("Publikationsdatum")
    assert not browser.is_text_present("Öffentlich")

    # enter a publication date in the past (no type date support in selenium)
    # set as the time of the layout timezone. UTC date can be a day before
    browser.find_by_name('hour').select('00:00')

    assert browser.is_text_present("Wird publiziert am", wait_time=1)
    assert not browser.is_text_present("Publikationsdatum")

    f = FileCollection(org_app.session()).query().one()
    dt = datetime.today()
    midnight = datetime(dt.year, dt.month, dt.day, 0, tzinfo=UTC)

    assert f.publish_date in (
        midnight,                        # utc
        midnight - timedelta(hours=1),   # +1:00 winter, Europe
        midnight - timedelta(hours=2)    # +2:00 summer, Europa
    )

    # run the cronjob and make sure it works
    job = org_app.config.cronjob_registry.cronjobs['hourly_maintenance_tasks']
    job.app = org_app
    job_url = f'{browser.url.replace("/files", "")}/cronjobs/{job.id}'

    requests.get(job_url)
    sleep(0.1)

    r = requests.get(file_url)
    assert r.status_code == 200
    assert 'public' in r.headers['cache-control']


def test_signature_workflow(browser, temporary_path, org_app):
    path = module_path('tests.onegov.org', 'fixtures/sample.pdf')
    org_app.enable_yubikey = True

    # upload the pdf
    browser.login_admin()
    browser.visit('/files')
    browser.drop_file('.upload-dropzone', path)

    assert browser.is_text_present("Soeben hochgeladen")

    # show the details
    browser.find_by_css('.upload-filelist .untoggled').click()
    assert browser.is_text_present("Ohne digitales Siegel")

    # try to sign the pdf (this won't work in this test-environment due to
    # it being in a different process, but we should see the error handling)
    browser.find_by_css('a.is-not-signed').click()

    assert browser.is_text_present("Bitte geben Sie Ihren Yubikey ein")
    assert browser.is_text_present("Signieren")

    browser.find_by_css('.dialog input').fill('foobar')
    browser.find_by_text("Signieren").click()

    assert browser.is_text_present("nicht mit einem Yubikey verknüpft")

    # change the database and show the information in the browser
    f = FileCollection(org_app.session()).query().one()
    f.signed = True
    f.signature_metadata = {
        'signee': 'foo@example.org',
        'timestamp': utcnow().isoformat()
    }
    transaction.commit()

    # make sure the signature information is shown
    browser.visit('/files')
    browser.find_by_css('.untoggled').click()

    assert browser.is_text_present('foo@example.org')
    assert browser.is_text_present('Digitales Siegel angewendet')
