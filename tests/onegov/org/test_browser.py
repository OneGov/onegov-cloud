from __future__ import annotations

import niquests
import os
import pytest
import time
import transaction

from datetime import datetime, timedelta
from onegov.core.utils import module_path
from onegov.directory import DirectoryCollection
from onegov.file import FileCollection
from onegov.org.models import (
    ImageFileCollection,
    ImageSetCollection,
    ResourceRecipientCollection,
)
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
    from playwright.sync_api import Locator
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
    browser.find_by_text("Speichern").click()

    assert browser.is_text_present("Seven Seas Motel")
    assert browser.is_element_present_by_css('.field-display img')

    src = browser.find_by_css('.field-display img')['src']

    # elect to keep the picture (default)
    browser.find_by_css('.edit-link').click()
    browser.fill('name', "Seven Seas Motel, Miami")
    browser.find_by_text("Speichern").click()

    assert browser.is_text_present("Seven Seas Motel, Miami")
    assert browser.is_element_present_by_css('.field-display img')
    assert browser.find_by_css('.field-display img')['src'] == src

    # elect to replace the picture
    photo = create_image(output=NamedTemporaryFile(suffix='.png'))

    browser.find_by_css('.edit-link').click()
    browser.choose('photo', 'replace')
    browser.find_by_name('photo')[3].value = photo.name
    browser.find_by_text("Speichern").click()

    assert browser.is_element_present_by_css('.field-display img')
    assert browser.find_by_css('.field-display img')['src'] != src

    # elect to delete the picture
    browser.find_by_css('.edit-link').click()
    browser.choose('photo', 'delete')
    browser.find_by_text("Speichern").click()

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
    browser.find_by_text("Speichern").click()

    assert browser.is_text_present("Dieses Feld wird benötigt")

    # try again with the missing field present
    browser.fill('description', "First victim of Ice Truck Killer")
    browser.find_by_text("Speichern").click()

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
    browser.find_by_text("Absenden").click()


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
    submit = browser.find_by_text("Absenden")
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
    browser.find_by_text("Speichern").click()

    browser.visit('/directories/restaurants/+new')
    browser.fill('name', "City Sushi")
    browser.fill('tables', "20")
    assert browser.is_element_present_by_css('.add-point-active', wait_time=5)
    browser.execute_script('document.leafletmaps[0].panBy([100, -100]);')
    browser.find_by_css('.add-point-active').click()
    browser.find_by_text("Speichern").click()

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
    assert file_url is not None
    r = niquests.get(file_url, timeout=10)
    assert r.status_code == 200
    assert 'public' in r.headers['cache-control']

    # make sure unpublishing works
    browser.find_by_css('.publication .file-status-tag a').click()
    r = niquests.get(file_url, timeout=10)
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

    niquests.get(job_url, timeout=10)
    sleep(0.1)

    r = niquests.get(file_url, timeout=10)
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

    browser.find_by_text("Speichern").click()
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
    browser.find_by_text("Speichern").click()

    browser.visit(f"/person/{person.id.hex}")
    browser.find_by_text('All About Berry: Logician')


@pytest.mark.xdist_group(name="browser")
def test_blocknote_editor_roundtrip(
    browser: ExtendedBrowser,
    org_app: TestOrgApp,
) -> None:
    org_app.infomaniak_api_token = 'blocknote-ai-test-token'
    org_app.infomaniak_product_id = 'blocknote-ai-test-product'
    album = ImageSetCollection(org_app.session()).add(title='Sommerfest')
    album_image = ImageFileCollection(org_app.session()).add(
        'sommerfest.png',
        create_image().read(),
        note='Sommerfest Bild',
    )
    album.files = [album_image]
    transaction.commit()

    browser.login_admin()
    browser.visit('/editor/new/page/1')

    wrapper = browser.page.locator(
        '.field-text .onegov-blocknote-wrapper'
        '[data-onegov-blocknote-wrapper]'
    )
    wrapper.wait_for(timeout=15_000)
    editor = wrapper.locator('[data-onegov-blocknote-editor]')
    editor.wait_for(timeout=15_000)

    source_field = browser.page.locator('.field-text textarea.editor')
    assert source_field.get_attribute('aria-hidden') == 'true'
    assert browser.page.locator('.redactor-editor').count() == 0

    ai_styles = browser.page.evaluate("""() => {
        const host = document.createElement('div');
        host.className = 'onegov-blocknote-view';
        host.style.setProperty('--onegov-primary-color', '#006fba');
        host.innerHTML = `
            <div class="bn-editor">
                <ins data-id="1" data-inline="true">Added</ins>
                <span data-id="2" data-type="modification">Changed</span>
                <del data-id="3" data-inline="true">Removed</del>
            </div>`;
        document.body.append(host);
        const added = getComputedStyle(host.querySelector('ins'));
        const changed = getComputedStyle(host.querySelector(
            '[data-type="modification"]'
        ));
        const removed = getComputedStyle(host.querySelector('del'));
        const result = {
            addedBackground: added.backgroundColor,
            addedBorder: added.borderBottomColor,
            changedDecoration: changed.textDecorationStyle,
            removedBackground: removed.backgroundColor,
            removedDecoration: removed.textDecorationLine,
        };
        host.remove();
        return result;
    }""")
    assert ai_styles['addedBackground'] not in (
        'rgba(0, 0, 0, 0)',
        'rgb(255, 255, 255)',
    )
    assert ai_styles['addedBorder'] == 'rgb(0, 111, 186)'
    assert ai_styles['changedDecoration'] == 'dashed'
    assert ai_styles['removedBackground'] == 'rgb(253, 236, 236)'
    assert ai_styles['removedDecoration'] == 'line-through'

    # The toolbar is displayed below the editor and must not intercept the
    # normal tab order when entering the rich-text field.
    toolbar = wrapper.locator('.onegov-blocknote-toolbar')
    toolbar_box = toolbar.bounding_box()
    editor_box = editor.bounding_box()
    assert toolbar_box and editor_box
    assert toolbar_box['y'] > editor_box['y']
    browser.page.locator('[name="lead"]').focus()
    browser.page.keyboard.press('Tab')
    assert editor.evaluate('element => document.activeElement === element')

    browser.fill('title', 'BlockNote Roundtrip')
    editor.locator('.bn-inline-content').first.click()
    wrapper.locator('[data-onegov-blocknote-control="undo"]').click()
    assert editor.evaluate('element => document.activeElement === element')

    wrapper.locator('button[title="HTML"]').click()
    wrapper.locator('.onegov-blocknote-dialog textarea').wait_for()
    browser.page.keyboard.press('Escape')
    assert editor.evaluate('element => document.activeElement === element')

    wrapper.locator('button[title="HTML"]').click()
    source = wrapper.locator('.onegov-blocknote-dialog textarea')
    source.fill(
        '<h2>Heading</h2>'
        '<p>Delete me</p>'
        '<p><strong>Bold</strong>, <em>italic</em>, '
        '<del>deleted</del>, H<sub>2</sub>O and x<sup>2</sup>.</p>'
        '<p class="edit-note">Editorial '
        '<a href="/topics/organisation" title="Home">note</a></p>'
        '<ol><li>Numeric</li></ol>'
        '<ol class="alpha-list"><li>First</li><li>Second</li></ol>'
        '<p>Break</p><ol class="alpha-list"><li>Restart</li></ol>'
        '<table><tbody><tr><th>Head</th><td>Cell</td></tr></tbody></table>'
        '<pre>&lt;example&gt;</pre>'
    )
    wrapper.locator(
        '.onegov-blocknote-dialog-actions .button:not(.secondary)'
    ).click()

    editor.locator(
        '.bn-block-content[data-content-type="paragraph"] .bn-inline-content'
    ).first.wait_for(timeout=5_000)
    editor.locator(
        '.bn-block-content[data-content-type="paragraph"] .bn-inline-content',
        has_text='Bold',
    ).select_text()
    formatting_toolbar = browser.page.locator('.bn-formatting-toolbar')
    formatting_toolbar.wait_for(timeout=5_000)
    assert formatting_toolbar.locator('[data-test="createLink"]').count() == 1
    assert formatting_toolbar.get_by_role(
        'button', name='Mit KI bearbeiten'
    ).count() == 1
    assert formatting_toolbar.get_by_role(
        'button', name='Hochgestellt'
    ).count() == 1
    assert formatting_toolbar.get_by_role(
        'button', name='Tiefgestellt'
    ).count() == 1

    formatting_toolbar.get_by_text('Absatz', exact=True).click()
    browser.page.get_by_text('Überschrift 2', exact=True).click()
    formatted_block = editor.locator(
        '.bn-block-content[data-content-type="heading"]',
        has_text='Bold',
    )
    heading = formatted_block.locator('h2')
    assert heading.count() == 1
    heading_size = heading.evaluate(
        'element => parseFloat(getComputedStyle(element).fontSize)'
    )
    paragraph_size = editor.locator(
        '.bn-block-content[data-content-type="paragraph"] .bn-inline-content',
        has_text='Delete me',
    ).evaluate('element => parseFloat(getComputedStyle(element).fontSize)')
    assert heading_size > paragraph_size
    formatted_block.locator('.bn-inline-content').select_text()
    formatting_toolbar.get_by_text('Überschrift 2', exact=True).click()
    browser.page.get_by_text('Absatz', exact=True).click()
    paragraph_block = editor.locator(
        '.bn-block-content[data-content-type="paragraph"]', has_text='Bold'
    )
    assert paragraph_block.count() == 1

    paragraph_block.locator('.bn-inline-content').select_text()
    formatting_toolbar.get_by_text('Absatz', exact=True).click()
    browser.page.get_by_text('Aufzählungsliste', exact=True).click()
    bullet_block = editor.locator(
        '.bn-block-content[data-content-type="bulletListItem"]',
        has_text='Bold',
    )
    assert bullet_block.evaluate(
        "element => getComputedStyle(element, '::before').content"
    ).strip('"') == '•'

    bullet_block.locator('.bn-inline-content').select_text()
    formatting_toolbar.get_by_text('Aufzählungsliste', exact=True).click()
    browser.page.get_by_text('Nummerierte Liste', exact=True).click()
    numbered_block = editor.locator(
        '.bn-block-content[data-content-type="numberedListItem"]',
        has_text='Bold',
    )
    assert numbered_block.evaluate(
        "element => getComputedStyle(element, '::before').content"
    ).strip('"') == '1.'

    numbered_block.locator('.bn-inline-content').select_text()
    formatting_toolbar.get_by_text('Nummerierte Liste', exact=True).click()
    browser.page.get_by_text('Zitat', exact=True).click()
    quote_block = editor.locator(
        '.bn-block-content[data-content-type="quote"]', has_text='Bold'
    )
    assert quote_block.locator('blockquote').count() == 1

    quote_block.locator('.bn-inline-content').select_text()
    formatting_toolbar.get_by_text('Zitat', exact=True).click()
    browser.page.get_by_text('Absatz', exact=True).click()
    paragraph_block = editor.locator(
        '.bn-block-content[data-content-type="paragraph"]', has_text='Bold'
    )
    assert paragraph_block.count() == 1

    # Creating a list through the side-menu plus uses a different BlockNote
    # insertion path than converting an existing paragraph.
    paragraph_block.hover()
    wrapper.locator('[data-test="dragHandleAdd"]').click()
    plus_menu = browser.page.locator('#bn-suggestion-menu').last
    plus_menu.wait_for(timeout=5_000)
    plus_menu.get_by_text('Aufzählungsliste', exact=True).click()
    browser.page.wait_for_function(
        """() => {
            const editor = document.querySelector(
                '[data-onegov-blocknote-editor]'
            );
            return editor?.contains(document.activeElement);
        }"""
    )
    assert editor.evaluate(
        'element => element.contains(document.activeElement)'
    )
    added_bullet = editor.locator(
        '.bn-block-content[data-content-type="bulletListItem"]'
    ).last
    assert added_bullet.evaluate(
        "element => getComputedStyle(element, '::before').content"
    ).strip('"') == '•'
    added_bullet.locator('.bn-inline-content').fill('Added list item')

    added_bullet.hover()
    wrapper.locator('[data-test="dragHandleAdd"]').click()
    plus_menu.wait_for(timeout=5_000)
    plus_menu.get_by_text('Überschrift 2', exact=True).click()
    browser.page.wait_for_function(
        """() => document.querySelector(
            '[data-onegov-blocknote-editor]'
        )?.contains(document.activeElement)"""
    )
    assert editor.evaluate(
        'element => element.contains(document.activeElement)'
    )
    added_heading = editor.locator(
        '.bn-block-content[data-content-type="heading"]'
    ).last
    assert added_heading.locator('h2').count() == 1
    assert added_heading.evaluate(
        'element => parseFloat(getComputedStyle(element).fontSize)'
    ) > paragraph_size
    added_heading.locator('.bn-inline-content').fill('Added heading')

    added_heading.hover()
    wrapper.locator('[data-test="dragHandleAdd"]').click()
    plus_menu.wait_for(timeout=5_000)
    assert plus_menu.get_by_text('Überschrift 4', exact=True).count() == 1
    assert plus_menu.get_by_text('Überschrift 5', exact=True).count() == 1
    plus_menu.get_by_text('Überschrift 4', exact=True).click()
    added_subheading = editor.locator(
        '.bn-block-content[data-content-type="heading"]'
    ).last
    assert added_subheading.locator('h4').count() == 1
    assert added_subheading.evaluate(
        'element => parseFloat(getComputedStyle(element).fontSize)'
    ) > paragraph_size
    added_subheading.locator('.bn-inline-content').fill('Added subheading')

    added_subheading.hover()
    wrapper.locator('[data-test="dragHandleAdd"]').click()
    plus_menu.wait_for(timeout=5_000)
    assert plus_menu.get_by_text(
        'Aufklappbare Überschrift 2', exact=True
    ).count() == 1
    assert plus_menu.get_by_text(
        'Aufklappbare Überschrift 3', exact=True
    ).count() == 1
    plus_menu.get_by_text(
        'Aufklappbare Überschrift 2', exact=True
    ).click()
    browser.page.wait_for_function(
        """() => document.querySelector(
            '[data-onegov-blocknote-editor]'
        )?.contains(document.activeElement)"""
    )
    added_toggle = editor.locator(
        '.bn-block-content[data-content-type="heading"]'
        '[data-is-toggleable="true"]'
    ).last
    assert added_toggle.locator('h2').count() == 1
    assert added_toggle.locator('h2').evaluate(
        'element => parseFloat(getComputedStyle(element).fontSize)'
    ) > paragraph_size
    toggle_block = added_toggle.locator('..')
    assert toggle_block.evaluate(
        "element => getComputedStyle(element).backgroundColor"
    ) != 'rgba(0, 0, 0, 0)'
    assert toggle_block.evaluate(
        "element => getComputedStyle(element).borderTopStyle"
    ) == 'solid'
    added_toggle.locator('.bn-inline-content').fill('Toggle heading')
    toggle_wrapper = added_toggle.locator('.bn-toggle-wrapper')
    browser.page.wait_for_function(
        "element => element.dataset.showChildren === 'true'",
        arg=toggle_wrapper.element_handle(),
    )
    assert added_toggle.locator('.bn-toggle-button').evaluate(
        "element => getComputedStyle(element).display"
    ) == 'none'
    add_toggle_child = added_toggle.locator('.bn-toggle-add-block-button')
    add_toggle_child.wait_for(timeout=5_000)
    add_toggle_child.click()
    toggle_children = toggle_block.locator(':scope > .bn-block-group')
    toggle_child = toggle_children.locator('.bn-inline-content').first
    toggle_child.fill('Toggle content')
    toggle_child.click()
    browser.page.wait_for_timeout(50)
    assert toggle_wrapper.get_attribute('data-show-children') == 'true'
    browser.page.keyboard.type(' edited')
    assert ' edited' in (toggle_child.text_content() or '')
    assert toggle_children.evaluate(
        "element => getComputedStyle(element).borderTopStyle"
    ) == 'solid'
    assert toggle_block.evaluate(
        "element => getComputedStyle(element).borderRadius"
    ) == '8px'
    deletable = editor.locator(
        '.bn-block-content[data-content-type="paragraph"]',
        has_text='Delete me',
    )
    deletable.hover()
    wrapper.locator(
        '.bn-side-menu button[aria-label="Blockmenü öffnen"]'
    ).click()
    drag_handle_menu = browser.page.locator('.bn-drag-handle-menu')
    assert drag_handle_menu.get_by_text('Farben', exact=True).count() == 0
    drag_handle_menu.locator('.bn-menu-item', has_text='Löschen').click()
    assert deletable.count() == 0
    assert 'Delete me' not in source_field.input_value()

    alpha_item = editor.locator(
        '.bn-block-content[data-content-type="numberedListItem"] '
        '.bn-inline-content'
    ).nth(2)
    alpha_item.fill('Second changed')
    browser.page.wait_for_timeout(100)
    restart_item = editor.locator(
        '.bn-block-content[data-content-type="numberedListItem"] '
        '.bn-inline-content'
    ).nth(3)
    alpha_marker = alpha_item.locator('..').evaluate(
        "element => getComputedStyle(element, '::before').content"
    )
    restart_marker = restart_item.locator('..').evaluate(
        "element => getComputedStyle(element, '::before').content"
    )
    assert alpha_marker.strip('"') == 'b.'
    assert restart_marker.strip('"') == 'a.'

    assert wrapper.locator(
        '[data-onegov-blocknote-control="image"], '
        '[data-onegov-blocknote-control="file"], '
        '[data-onegov-blocknote-control="internal"]'
    ).count() == 0
    assert wrapper.locator(
        '[data-onegov-blocknote-control="undo"], '
        '[data-onegov-blocknote-control="redo"], '
        '[data-onegov-blocknote-control="html"]'
    ).count() == 3

    def open_slash_menu() -> Locator:
        break_block = editor.locator(
            '.bn-block-content[data-content-type="paragraph"] '
            '.bn-inline-content',
            has_text='Break',
        )
        break_block.evaluate("""
            element => {
                element.focus();
                const range = document.createRange();
                const selection = window.getSelection();
                range.selectNodeContents(element);
                range.collapse(false);
                selection.removeAllRanges();
                selection.addRange(range);
            }
        """)
        browser.page.keyboard.press('Enter')
        browser.page.keyboard.type('/')
        menu = browser.page.locator('#bn-suggestion-menu')
        menu.wait_for(timeout=5_000)
        return menu

    slash_menu = open_slash_menu()
    assert slash_menu.get_by_text('Bild', exact=True).count() == 1
    assert slash_menu.get_by_text('Datei', exact=True).count() == 1
    assert slash_menu.get_by_text('Interner Link', exact=True).count() == 1
    assert slash_menu.get_by_text('Fotoalbum', exact=True).count() == 1
    assert slash_menu.get_by_text('KI fragen', exact=True).count() == 1

    open_slash_menu().get_by_text('Tabelle', exact=True).click()
    assert editor.locator(
        '.bn-block-content[data-content-type="table"]'
    ).count() == 2
    inserted_table = editor.locator(
        '.bn-block-content[data-content-type="table"]'
    ).first
    inserted_cells = inserted_table.locator('td')
    assert inserted_cells.count() == 6
    for index, cell_text in enumerate((
        'Und Text',
        'Und mehr',
        'Und noch mehr',
    )):
        inserted_cells.nth(index).click()
        browser.page.keyboard.type(cell_text)
    assert '<colgroup>' in source_field.input_value()

    open_slash_menu().get_by_text('Bild', exact=True).click()
    picker = browser.page.locator('.onegov-resource-picker-overlay')
    picker.wait_for(timeout=5_000)
    picker.locator('.onegov-resource-picker-close').click()
    picker.wait_for(state='detached', timeout=5_000)
    assert editor.locator(
        '.bn-block-content[data-content-type="image"]'
    ).count() == 0

    image = create_image(
        width=80,
        height=80,
        output=NamedTemporaryFile(suffix='.png'),
    )
    open_slash_menu().get_by_text('Bild', exact=True).click()
    upload_input = browser.page.locator(
        '.onegov-resource-picker-upload input[type="file"]'
    )
    upload_input.set_input_files(image.name)
    crop_dialog = browser.page.locator('.onegov-image-crop-dialog')
    crop_dialog.wait_for(timeout=5_000)
    crop_area = crop_dialog.locator('.reactEasyCrop_CropArea')
    crop_area.wait_for(timeout=5_000)
    crop_box = crop_area.bounding_box()
    assert crop_box
    assert abs(crop_box['width'] / crop_box['height'] - 4 / 3) < 0.01
    cancel_crop = crop_dialog.get_by_role('button', name='Abbrechen')
    assert cancel_crop.evaluate(
        'element => document.activeElement === element'
    )
    cancel_crop.click()
    crop_dialog.wait_for(state='detached', timeout=5_000)
    assert browser.page.locator('.onegov-resource-picker-overlay').count() == 1
    assert editor.locator(
        '.bn-block-content[data-content-type="image"]'
    ).count() == 0

    upload_input.set_input_files(image.name)
    crop_dialog.wait_for(timeout=5_000)
    crop_dialog.locator('input[name="image-crop-zoom"]').fill('1.2')
    crop_dialog.locator('input[name="image-crop-rotation"]').fill('10')
    crop_dialog.get_by_role('button', name='Übernehmen').click()
    browser.page.locator('.onegov-resource-picker-overlay').wait_for(
        state='detached', timeout=15_000
    )
    inserted_image = editor.locator(
        '.bn-block-content[data-content-type="image"]'
    )
    assert inserted_image.count() == 1
    inserted_preview = inserted_image.locator('img')
    inserted_preview.wait_for(timeout=5_000)
    browser.page.wait_for_function(
        'element => element.naturalWidth > 0',
        arg=inserted_preview.element_handle(),
    )
    inserted_size = inserted_preview.evaluate(
        'element => [element.naturalWidth, element.naturalHeight]'
    )
    assert abs(inserted_size[0] / inserted_size[1] - 4 / 3) < 0.03
    inserted_image.click()
    formatting_toolbar = browser.page.locator('.bn-formatting-toolbar')
    formatting_toolbar.wait_for(timeout=5_000)
    assert formatting_toolbar.get_by_role(
        'button', name='Hochgestellt'
    ).count() == 0
    assert formatting_toolbar.get_by_role(
        'button', name='Tiefgestellt'
    ).count() == 0
    assert formatting_toolbar.get_by_role(
        'button', name='Mit KI bearbeiten'
    ).count() == 0
    formatting_toolbar.get_by_role(
        'button', name='Beschriftung bearbeiten'
    ).click()
    caption_input = browser.page.locator('input[name="file-caption"]')
    caption_input.fill('Sommerfest am See')
    browser.page.keyboard.press('Enter')
    assert inserted_image.locator(
        'figcaption.bn-file-caption', has_text='Sommerfest am See'
    ).count() == 1

    open_slash_menu().get_by_text('Fotoalbum', exact=True).click()
    album_picker = browser.page.locator('.onegov-resource-picker-overlay')
    album_picker.wait_for(timeout=5_000)
    album_choice = album_picker.locator(
        '.onegov-resource-picker-choice[aria-label="Sommerfest"]'
    )
    album_choice.wait_for(timeout=15_000)
    assert album_picker.locator(
        '.onegov-resource-picker-choice[aria-label="Organisation"]'
    ).count() == 0
    album_choice.click()
    album_block = editor.locator(
        '.bn-block-content[data-content-type="photoAlbum"]',
        has_text='Sommerfest',
    )
    assert album_block.count() == 1
    assert 'onegov-photoalbum-block' in source_field.input_value()

    open_slash_menu().get_by_text('Datei', exact=True).click()
    browser.page.locator(
        '.onegov-resource-picker-upload input[type="file"]'
    ).set_input_files(module_path('tests.onegov.org', 'fixtures/sample.pdf'))
    browser.page.locator('.onegov-resource-picker-overlay').wait_for(
        state='detached', timeout=15_000
    )
    assert editor.locator(
        '.bn-block-content[data-content-type="file"]', has_text='sample.pdf'
    ).count() == 1

    open_slash_menu().get_by_text('Interner Link', exact=True).click()
    internal_choice = browser.page.locator(
        '.onegov-resource-picker-choice'
    ).first
    internal_choice.wait_for(timeout=15_000)
    internal_label = internal_choice.get_attribute('aria-label')
    assert internal_label
    internal_choice.click()
    internal_block = editor.locator(
        '.bn-block-content[data-content-type="paragraph"] a',
        has_text=internal_label,
    )
    assert internal_block.count() == 1

    # The submit listener must synchronously serialize the latest document.
    browser.find_by_text('Speichern').click()
    browser.page.wait_for_url('**/topics/organisation/blocknote-roundtrip')

    assert browser.page.get_by_role(
        'heading', name='Heading', exact=True, level=2
    ).count() == 1
    assert browser.page.get_by_role(
        'heading', name='Added heading', exact=True, level=2
    ).count() == 1
    assert browser.page.get_by_role(
        'heading', name='Added subheading', exact=True, level=4
    ).count() == 1
    rendered_toggle = browser.page.locator(
        '.page-text details', has_text='Toggle heading'
    )
    assert not rendered_toggle.evaluate('element => element.open')
    assert rendered_toggle.locator(
        ':scope > summary > h2', has_text='Toggle heading'
    ).count() == 1
    rendered_toggle_content = rendered_toggle.locator(':scope > p')
    assert rendered_toggle_content.count() == 1
    assert not rendered_toggle_content.is_visible()
    assert ' edited' in (rendered_toggle_content.text_content() or '')
    assert rendered_toggle.evaluate(
        "element => getComputedStyle(element).borderRadius"
    ) == '8px'
    rendered_summary = rendered_toggle.locator(':scope > summary')
    rendered_summary.click()
    assert rendered_toggle.evaluate('element => element.open')
    assert rendered_toggle_content.is_visible()
    assert rendered_summary.evaluate(
        "element => getComputedStyle(element).borderBottomStyle"
    ) == 'solid'
    assert rendered_summary.evaluate(
        "element => getComputedStyle(element, '::after').borderTopColor"
    ) == 'rgb(0, 111, 186)'
    assert browser.page.locator('strong', has_text='Bold').count() == 1
    assert browser.page.locator('em', has_text='italic').count() == 1
    assert browser.page.locator('del', has_text='deleted').count() == 1
    assert browser.page.locator('sub', has_text='2').count() == 1
    assert browser.page.locator('sup', has_text='2').count() == 1
    assert browser.page.locator(
        'p.edit-note a[href="/topics/organisation"]', has_text='note'
    ).count() == 1
    assert browser.page.locator(
        'ol.alpha-list > li', has_text='Second changed'
    ).count() == 1
    assert browser.page.locator(
        'ol.alpha-list > li', has_text='Restart'
    ).count() == 1
    assert browser.page.locator('ol.alpha-list').count() == 2
    assert browser.page.locator(
        'ol:not(.alpha-list) > li', has_text='Numeric'
    ).count() == 1
    assert browser.page.locator(
        'ul > li', has_text='Added list item'
    ).count() == 1
    assert browser.page.locator(
        '.page-text a', has_text='sample.pdf'
    ).count() == 1
    assert browser.page.locator(
        '.page-text a', has_text=internal_label
    ).count() >= 1
    assert browser.page.locator('.page-text img').count() == 2
    standalone_figure = browser.page.locator(
        '.page-text figure', has_text='Sommerfest am See'
    )
    figure_margins = standalone_figure.evaluate(
        'element => {'
        '  const style = getComputedStyle(element);'
        '  return [parseFloat(style.marginTop), '
        'parseFloat(style.marginBottom)];'
        '}'
    )
    assert figure_margins[0] > 0
    assert figure_margins[1] > figure_margins[0]
    standalone_caption = standalone_figure.locator(
        'figcaption', has_text='Sommerfest am See'
    )
    assert standalone_caption.count() == 1
    assert standalone_caption.evaluate(
        'element => getComputedStyle(element).backgroundColor'
    ) == 'rgba(0, 0, 0, 0)'
    assert standalone_caption.evaluate(
        'element => parseFloat(getComputedStyle(element).paddingTop)'
    ) > 0
    assert standalone_figure.locator('.alt-text').count() == 0
    standalone_image = standalone_figure.locator('img')
    assert standalone_image.get_attribute('alt') == 'Sommerfest am See'
    assert standalone_image.evaluate(
        "element => element.closest('.photoswipe') !== null"
    )
    standalone_image.click()
    lightbox = browser.page.locator('.pswp.pswp--open')
    lightbox.wait_for(timeout=5_000)
    assert lightbox.locator(
        '.pswp__caption:not(.pswp__caption--fake)',
        has_text='Sommerfest am See',
    ).is_visible()
    browser.page.wait_for_function(
        "element => element.classList.contains('pswp--animated-in')",
        arg=lightbox.element_handle(),
    )
    browser.page.keyboard.press('Escape')
    lightbox.wait_for(state='hidden', timeout=5_000)
    assert browser.page.locator(
        '.grid-imageset.photoswipe img[alt="Sommerfest Bild"]'
    ).count() == 1
    assert browser.page.locator(
        '.grid-imageset.photoswipe .alt-text', has_text='Sommerfest Bild'
    ).count() == 1
    assert browser.page.locator(
        '.grid-imageset.photoswipe .alt-text', has_text='Sommerfest Bild'
    ).evaluate(
        'element => getComputedStyle(element).backgroundColor'
    ) == 'rgba(0, 0, 0, 0)'
    assert browser.page.evaluate(
        '() => typeof window.PhotoSwipe === "function"'
    )
    assert browser.page.locator('table th', has_text='Head').count() == 1
    assert browser.page.locator('table td', has_text='Cell').count() == 1
    rendered_table = browser.page.locator('table', has_text='Und Text')
    assert rendered_table.count() == 1
    assert rendered_table.locator('colgroup > col').count() == 3
    assert rendered_table.locator('td', has_text='Und mehr').count() == 1
    assert all(
        '<colgroup>' not in text
        for text in browser.page.locator('.page-text').all_text_contents()
    )
    assert browser.page.locator('pre', has_text='<example>').count() == 1
    assert browser.page.get_by_text('Delete me', exact=True).count() == 0

    # Saving an editor that was not touched must retain accepted legacy HTML
    # that BlockNote does not model as a native inline style.
    legacy_markup = (
        '<p><abbr title="Legacy abbreviation">Legacy</abbr> '
        '<span>content</span></p><p>Other</p>'
    )
    browser.find_by_css('.edit-link').click()
    wrapper = browser.page.locator(
        '.field-text .onegov-blocknote-wrapper'
        '[data-onegov-blocknote-wrapper]'
    )
    wrapper.wait_for(timeout=15_000)
    reopened_editor = wrapper.locator('[data-onegov-blocknote-editor]')
    assert reopened_editor.locator(
        '.bn-block-content[data-content-type="image"]'
    ).count() == 1
    assert reopened_editor.locator(
        '.bn-block-content[data-content-type="image"] '
        'figcaption.bn-file-caption',
        has_text='Sommerfest am See',
    ).count() == 1
    assert reopened_editor.locator(
        '.bn-block-content[data-content-type="file"]', has_text='sample.pdf'
    ).count() == 1
    assert reopened_editor.locator(
        '.bn-block-content[data-content-type="photoAlbum"]',
        has_text='Sommerfest',
    ).count() == 1
    assert reopened_editor.locator(
        '.bn-block-content[data-content-type="heading"]'
        '[data-is-toggleable="true"]',
        has_text='Toggle heading',
    ).count() == 1
    assert reopened_editor.locator(
        '.bn-block-content[data-content-type="paragraph"] a',
        has_text=internal_label,
    ).count() == 1
    wrapper.locator('button[title="HTML"]').click()
    wrapper.locator('.onegov-blocknote-dialog textarea').fill(legacy_markup)
    wrapper.locator(
        '.onegov-blocknote-dialog-actions .button:not(.secondary)'
    ).click()
    browser.find_by_text('Speichern').click()
    browser.page.wait_for_url('**/topics/organisation/blocknote-roundtrip')
    assert browser.page.locator(
        'abbr[title="Legacy abbreviation"]', has_text='Legacy'
    ).count() == 1

    browser.find_by_css('.edit-link').click()
    wrapper = browser.page.locator(
        '.field-text .onegov-blocknote-wrapper'
        '[data-onegov-blocknote-wrapper]'
    )
    wrapper.wait_for(timeout=15_000)
    browser.fill('title', 'BlockNote Untouched')
    browser.find_by_text('Speichern').click()
    browser.page.wait_for_url('**/topics/organisation/blocknote-roundtrip')
    assert browser.page.locator(
        'abbr[title="Legacy abbreviation"]', has_text='Legacy'
    ).count() == 1
    assert browser.page.locator('.page-text span', has_text='content').count()

    # Editing a sibling block must not flatten untouched legacy markup.
    browser.find_by_css('.edit-link').click()
    wrapper = browser.page.locator(
        '.field-text .onegov-blocknote-wrapper'
        '[data-onegov-blocknote-wrapper]'
    )
    wrapper.wait_for(timeout=15_000)
    paragraph = wrapper.locator(
        '.bn-block-content[data-content-type="paragraph"] .bn-inline-content'
    ).nth(1)
    paragraph.fill('Other changed')
    browser.find_by_text('Speichern').click()
    browser.page.wait_for_url('**/topics/organisation/blocknote-roundtrip')
    assert browser.page.locator(
        'abbr[title="Legacy abbreviation"]', has_text='Legacy'
    ).count() == 1
    assert browser.page.locator(
        '.page-text p', has_text='Other changed'
    ).count() == 1


@pytest.mark.xdist_group(name="browser")
def test_blocknote_keeps_unsaved_block_edits(
    browser: ExtendedBrowser,
) -> None:
    browser.login_admin()
    browser.visit('/editor/new/page/1')
    browser.fill('title', 'Unsaved Block Edits')

    wrapper = browser.page.locator(
        '.field-text .onegov-blocknote-wrapper'
        '[data-onegov-blocknote-wrapper]'
    )
    wrapper.wait_for(timeout=15_000)
    editor = wrapper.locator('[data-onegov-blocknote-editor]')
    source_field = browser.page.locator('.field-text textarea.editor')

    wrapper.locator('button[title="HTML"]').click()
    wrapper.locator('.onegov-blocknote-dialog textarea').fill(
        '<p><abbr title="Legacy abbreviation">First block</abbr></p>'
        '<p>Second block</p>'
    )
    wrapper.locator(
        '.onegov-blocknote-dialog-actions .button:not(.secondary)'
    ).click()

    paragraphs = editor.locator(
        '.bn-block-content[data-content-type="paragraph"] '
        '.bn-inline-content'
    )
    paragraphs.nth(1).fill('Second block changed before save')
    paragraphs.nth(0).click()

    assert '<abbr title="Legacy abbreviation">' in source_field.input_value()
    assert 'Second block changed before save' in source_field.input_value()

    browser.find_by_text('Speichern').click()
    browser.page.wait_for_url('**/topics/organisation/unsaved-block-edits')
    assert browser.page.locator(
        'abbr[title="Legacy abbreviation"]', has_text='First block'
    ).count() == 1
    assert browser.page.get_by_text(
        'Second block changed before save', exact=True
    ).count() == 1
    browser.find_by_css('.edit-link').click()

    wrapper = browser.page.locator(
        '.field-text .onegov-blocknote-wrapper'
        '[data-onegov-blocknote-wrapper]'
    )
    wrapper.wait_for(timeout=15_000)
    editor = wrapper.locator('[data-onegov-blocknote-editor]')
    source_field = browser.page.locator('.field-text textarea.editor')

    paragraphs = editor.locator(
        '.bn-block-content[data-content-type="paragraph"] '
        '.bn-inline-content'
    )
    first = paragraphs.nth(0)
    second = paragraphs.nth(1)
    first.fill('First block changed')
    second.click()

    assert first.text_content() == 'First block changed'
    assert 'First block changed' in source_field.input_value()

    browser.find_by_text('Speichern').click()
    browser.page.wait_for_url('**/topics/organisation/unsaved-block-edits')
    assert browser.page.get_by_text('First block changed', exact=True).count()


@pytest.mark.xdist_group(name="browser")
def test_blocknote_deleting_last_block_serializes_empty(
    browser: ExtendedBrowser,
) -> None:
    browser.login_admin()
    browser.visit('/editor/new/page/1')
    browser.fill('title', 'BlockNote Empty')

    wrapper = browser.page.locator(
        '.field-text .onegov-blocknote-wrapper'
        '[data-onegov-blocknote-wrapper]'
    )
    wrapper.wait_for(timeout=15_000)
    editor = wrapper.locator('[data-onegov-blocknote-editor]')
    editor.wait_for(timeout=15_000)
    source_field = browser.page.locator('.field-text textarea.editor')

    wrapper.locator('button[title="HTML"]').click()
    wrapper.locator('.onegov-blocknote-dialog textarea').fill(
        '<p>Only block</p>'
    )
    wrapper.locator(
        '.onegov-blocknote-dialog-actions .button:not(.secondary)'
    ).click()

    only_block = editor.locator(
        '.bn-block-content[data-content-type="paragraph"]',
        has_text='Only block',
    )
    only_block.hover()
    wrapper.locator(
        '.bn-side-menu button[aria-label="Blockmenü öffnen"]'
    ).click()
    browser.page.locator(
        '.bn-drag-handle-menu .bn-menu-item', has_text='Löschen'
    ).click()

    assert only_block.count() == 0
    assert editor.locator(
        '.bn-block-content[data-content-type="paragraph"]'
    ).count() == 1
    assert editor.locator(
        '.bn-block-content[data-content-type="editNote"]'
    ).count() == 0
    assert source_field.input_value() == ''

    browser.find_by_text('Speichern').click()
    browser.page.wait_for_url('**/topics/organisation/blocknote-empty')
    assert browser.page.get_by_text('Only block', exact=True).count() == 0


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
    browser.find_by_text("Annehmen").click()

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
    browser.find_by_text("Reservation absagen").click()
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
    browser.find_by_text("Speichern").click()

    browser.visit('/directories/clubs')
    browser.find_by_text("Konfigurieren").click()

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
    browser.find_by_text("Speichern").click()
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
    browser.find_by_text("Speichern").click()
    browser.visit('/people/new')
    browser.fill('first_name', 'John')
    browser.fill('last_name', 'Doe')
    browser.find_by_css("#organisations_multiple_chosen").click()
    # Only select the sub-organisation this should select the top organisation
    # "Organisation 2" automatically
    browser.find_by_css(".chosen-results .active-result:nth-child(3)").click()
    browser.find_by_text("Speichern").click()

    assert browser.is_text_present("Organisation 2 - Sub-Organisation 2.1")
    assert not browser.is_text_present("Organisation 1")
