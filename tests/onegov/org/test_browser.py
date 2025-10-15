from __future__ import annotations

import os
import pytest
import requests
import time
import transaction

from datetime import datetime, timedelta
from onegov.core.utils import module_path
from onegov.directory import DirectoryCollection
from onegov.file import FileCollection
from onegov.org.models import ResourceRecipientCollection
from onegov.people import Person
from onegov.reservation import ResourceCollection
from onegov.ticket import TicketCollection
from pathlib import Path
from pytz import UTC
from sedate import utcnow
from tempfile import NamedTemporaryFile
from tests.onegov.org.test_views_resources import add_reservation
from tests.shared.utils import create_image, encode_map_value
from time import sleep


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared.browser import ExtendedBrowser
    from .conftest import Client, TestOrgApp


# FIXME: For some reason all the browser tests need to run on the same process
#        in order to succeed. We should figure what breaks things here. Some
#        wires are probably being crossed, but it's nothing too obvious, we
#        already use separate application ports for every test.
@pytest.mark.xdist_group(name="browser")
def test_browse_activities(browser: ExtendedBrowser) -> None:
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
@pytest.mark.xdist_group(name="browser")
def test_browse_directory_uploads(
    browser: ExtendedBrowser,
    org_app: TestOrgApp,
    field: str
) -> None:

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
    browser.find_by_value("Speichern").click()

    assert browser.is_text_present("Seven Seas Motel")
    assert browser.is_element_present_by_css('.field-display img')

    src = browser.find_by_css('.field-display img')['src']

    # elect to keep the picture (default)
    browser.find_by_css('.edit-link').click()
    browser.fill('name', "Seven Seas Motel, Miami")
    browser.find_by_value("Speichern").click()

    assert browser.is_text_present("Seven Seas Motel, Miami")
    assert browser.is_element_present_by_css('.field-display img')
    assert browser.find_by_css('.field-display img')['src'] == src

    # elect to replace the picture
    photo = create_image(output=NamedTemporaryFile(suffix='.png'))

    browser.find_by_css('.edit-link').click()
    browser.choose('photo', 'replace')
    browser.find_by_name('photo')[3].value = photo.name
    browser.find_by_value("Speichern").click()

    assert browser.is_element_present_by_css('.field-display img')
    assert browser.find_by_css('.field-display img')['src'] != src

    # elect to delete the picture
    browser.find_by_css('.edit-link').click()
    browser.choose('photo', 'delete')
    browser.find_by_value("Speichern").click()

    if field.startswith('Photo ='):
        assert not browser.is_element_present_by_css('.field-display img')
    else:
        assert browser.is_text_present("Dieses Feld wird benötigt")


@pytest.mark.xdist_group(name="browser")
def test_upload_image_with_error(
    browser: ExtendedBrowser,
    org_app: TestOrgApp
) -> None:

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
    browser.find_by_value("Speichern").click()

    assert browser.is_text_present("Dieses Feld wird benötigt")

    # try again with the missing field present
    browser.fill('description', "First victim of Ice Truck Killer")
    browser.find_by_value("Speichern").click()

    assert browser.is_text_present("Seven Seas Motel")

    # the image won't be there however (it gets cleared in between requests)
    assert not browser.is_element_present_by_css('.field-display img')


@pytest.mark.skip('Picture upload is needed to check scaling')
@pytest.mark.xdist_group(name="browser")
def test_directory_thumbnail_views(
    browser: ExtendedBrowser,
    org_app: TestOrgApp
) -> None:

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
@pytest.mark.xdist_group(name="browser")
def test_browse_directory_editor(
    browser: ExtendedBrowser,
    org_app: TestOrgApp
) -> None:
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


@pytest.mark.xdist_group(name="browser")
def test_browse_directory_coordinates(
    browser: ExtendedBrowser,
    org_app: TestOrgApp
) -> None:

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
    browser.find_by_value("Speichern").click()

    browser.visit('/directories/restaurants/+new')
    browser.fill('name', "City Sushi")
    browser.fill('tables', "20")
    assert browser.is_element_present_by_css('.add-point-active', wait_time=5)
    browser.execute_script('document.leafletmaps[0].panBy([100, -100]);')
    browser.find_by_css('.add-point-active').click()
    browser.find_by_value("Speichern").click()

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


@pytest.mark.xdist_group(name="browser")
@pytest.mark.skip_night_hours
def test_publication_workflow(
    browser: ExtendedBrowser,
    temporary_path: Path,
    org_app: TestOrgApp
) -> None:

    path = temporary_path / 'foo.txt'

    with path.open('w') as fp:
        fp.write('bar')

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


@pytest.mark.xdist_group(name="browser")
def test_signature_workflow(
    browser: ExtendedBrowser,
    temporary_path: Path,
    org_app: TestOrgApp
) -> None:

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
    f.signature_metadata = {  # type: ignore[assignment]
        'signee': 'foo@example.org',
        'timestamp': utcnow().isoformat()
    }
    transaction.commit()

    # make sure the signature information is shown
    browser.visit('/files')
    browser.find_by_css('.untoggled').click()

    assert browser.is_text_present('foo@example.org')
    assert browser.is_text_present('Digitales Siegel angewendet')


@pytest.mark.xdist_group(name="browser")
def test_external_map_link(
    browser: ExtendedBrowser,
    client: Client[TestOrgApp]
) -> None:

    client.login_admin()
    settings = client.get('/map-settings')
    settings.form['geo_provider'] = 'geo-bs'
    settings.form.submit()

    topic = client.get('/topics/themen')
    topic = topic.click('Bearbeiten')

    topic.form['coordinates'] = encode_map_value({
        'lat': 47.5, 'lon': 7.58, 'zoom': 6
    })
    topic.form.submit()

    browser.visit('/topics/themen')
    browser.find_by_css(".button-state").click()
    assert browser.is_text_present("Karte Geo-BS")


@pytest.mark.flaky(reruns=3, only_rerun=None)
@pytest.mark.xdist_group(name="browser")
def test_context_specific_function_are_displayed_in_person_directory(
    browser: ExtendedBrowser,
    client: Client[TestOrgApp]
) -> None:

    browser.login_admin()
    client.login_admin()
    browser.visit('/people/new')
    browser.fill_form({
        'first_name': 'Berry',
        'last_name': 'Boolean'
    })

    browser.find_by_value("Speichern").click()
    person = (
        client.app.session().query(Person)
        .filter(Person.last_name == 'Boolean')
        .one()
    )

    browser.visit('/editor/new/page/1')
    chosen_input = browser.find_by_id('people_0_person_chosen')
    chosen_input.click()
    search_input = chosen_input.find_by_xpath('.//input').first
    search_input.fill('Boolean Berry\t')
    browser.fill_form({
        'title': 'All About Berry',
        'people-0-context_specific_function': 'Logician',
        'people-0-display_function_in_person_directory': True,
    })
    browser.find_by_value("Speichern").click()

    browser.visit(f"/person/{person.id.hex}")
    browser.find_by_text('All About Berry: Logician')


@pytest.mark.flaky(reruns=3, only_rerun=None)
@pytest.mark.xdist_group(name="browser")
def test_rejected_reservation_sends_email_to_configured_recipients(
    browser: ExtendedBrowser,
    client: Client[TestOrgApp]
) -> None:

    resources = ResourceCollection(client.app.libres_context)
    dailypass = resources.add('Dailypass', 'Europe/Zurich', type='daypass')

    recipients = ResourceRecipientCollection(client.app.session())
    recipients.add(
        name='John',
        medium='email',
        address='john@example.org',
        rejected_reservations=True,
        resources=[
            dailypass.id.hex,
        ]
    )

    add_reservation(
        dailypass,
        client.app.session(),
        datetime(2017, 1, 6, 12),
        datetime(2017, 1, 6, 16),
    )
    transaction.commit()

    tickets = TicketCollection(client.app.session())
    assert tickets.query().count() == 1

    browser.login_admin()
    browser.visit('/tickets/ALL/open')
    browser.find_by_value("Annehmen").click()

    def is_advanced_dropdown_present() -> bool:
        e = [e for e in browser.find_by_tag("button") if 'Erweitert' in e.text]
        return len(e) == 1

    browser.wait_for(
        is_advanced_dropdown_present,
        timeout=5,
    )
    advanced_menu_options = browser.find_by_tag("button")
    next(e for e in advanced_menu_options if 'Erweitert' in e.text).click()
    browser.wait_for(
        lambda: browser.is_element_present_by_xpath(
            '//a['
            '@data-confirm="Möchten Sie diese Reservation wirklich absagen?"]'
        ),
        timeout=5,
    )
    reject_reservation = browser.find_by_xpath(
        '//a[@data-confirm="Möchten Sie diese Reservation wirklich absagen?"]'
    )[0]
    reject_reservation.click()
    # confirm dialog
    browser.find_by_value("Reservation absagen").click()
    assert browser.wait_for(
        lambda: browser.is_text_present("Die Reservation wurde abgelehnt"),
        timeout=5,
    )

    assert len(os.listdir(client.app.maildir)) == 1
    mail = Path(client.app.maildir) / os.listdir(client.app.maildir)[0]
    with open(mail, 'r') as file:
        mail_content = file.read()
        assert (
            "Die folgenden Reservationen mussten leider abgesagt werden:"
            in mail_content
        )


@pytest.mark.xdist_group(name="browser")
def test_script_escaped_in_user_submitted_html(
    browser: ExtendedBrowser,
    org_app: TestOrgApp
) -> None:

    # This test attempts to inject JS (should not succeed of course)
    payload = """<script>document.addEventListener('DOMContentLoaded', () =>
    document.body.insertAdjacentHTML('afterbegin',
    '<h1 id="foo">This text has been injected with JS!</h1>'));</script>"""

    browser.login_admin()

    DirectoryCollection(org_app.session(), type='extended').add(
        **{
            'title': 'Clubs',
            'lead': 'this is just a normal lead',
            'structure': 'name *= ___',
        },
        configuration="""
            title:
                - name
            order:
                - name
            display:
                content:
                    - name
        """,
    )

    transaction.commit()

    browser.visit('/directories/clubs')

    add_button = '.edit-bar .right-side.tiny.button'  # Hinzufügen
    new_directory_button = 'a.new-directory-entry'  # Verzeichnis
    browser.find_by_css(add_button).click()
    assert browser.wait_for(
        lambda: bool(browser.find_by_css(new_directory_button)),
        timeout=3,
    )
    browser.find_by_css(new_directory_button).click()

    browser.fill('name', "Seven Seas Motel")
    browser.find_by_value("Speichern").click()

    browser.visit('/directories/clubs')
    browser.find_by_value("Konfigurieren").click()

    browser.fill('title_format', "[name]")
    browser.fill('lead_format', f'the multiline{payload}\nlead')

    payload_h1_selector = 'h1#foo'  # CSS selector for the injected element
    time.sleep(1)
    assert not browser.find_by_css(payload_h1_selector)


@pytest.mark.xdist_group(name="browser")
def test_link_hashtags(
    browser: ExtendedBrowser,
    org_app: TestOrgApp
) -> None:

    browser.login_admin()

    DirectoryCollection(org_app.session(), type='extended').add(
        title="Crime Scenes",
        structure="""
            Name *= ___
            Description *= ...
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
        """,
        type='extended'
    )

    transaction.commit()

    browser.login_admin()
    browser.visit('/directories/crime-scenes/+new')
    browser.fill('name', "Seven Seas Motel")
    browser.fill('description',
                 """
                 #hotel Our rooms are #amazing! Check them out here:
                 https://www.seven-seas-motel.com/#rooms
                 https://www.seven-seas-motel.com/rooms#luxury-suite
                 #fantastic
                 """)
    browser.find_by_value("Speichern").click()
    assert browser.is_text_present("Seven Seas Motel")

    # Only hashtags should be links, URL anchors should not be seen as hashtags
    assert ('<a class="hashtag" href="/search?q=%23amazing">#amazing</a>'
            ) in browser.html
    assert ('<a class="hashtag" href="/search?q=%23fantastic">#fantastic</a>'
            ) in browser.html
    assert ('<a class="hashtag" href="/search?q=%23hotel">#hotel</a>'
            ) in browser.html
    assert ('<a class="hashtag" href="/search?q=%23rooms">#rooms</a>'
            ) not in browser.html
    assert ('<a class="hashtag" href="/search?q=%23luxury-suite">'
            '#luxury-suite</a>') not in browser.html


@pytest.mark.flaky(reruns=3)
@pytest.mark.xdist_group(name="browser")
def test_people_multiple_select(
    browser: ExtendedBrowser,
    org_app: TestOrgApp
) -> None:

    browser.login_admin()

    browser.visit('/people-settings')
    browser.fill('organisation_hierarchy', """
    - Organisation 1
    - Organisation 2:
      - Sub-Organisation 2.1
      - Sub-Organisation 2.2
    """)
    browser.find_by_value("Speichern").click()
    browser.visit('/people/new')
    browser.fill('first_name', 'John')
    browser.fill('last_name', 'Doe')
    browser.find_by_css("#organisations_multiple_chosen").click()
    # Only select the sub-organisation this should select the top organisation
    # "Organisation 2" automatically
    browser.find_by_css(".chosen-results .active-result:nth-child(3)").click()
    browser.find_by_value("Speichern").click()

    assert browser.is_text_present("Organisation 2 - Sub-Organisation 2.1")
    assert not browser.is_text_present("Organisation 1")
