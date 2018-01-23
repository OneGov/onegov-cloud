import pytest
import transaction

from onegov.directory import DirectoryCollection
from onegov_testing.utils import create_image
from tempfile import NamedTemporaryFile


def test_browse_activities(browser):
    # admins
    browser.login_admin()
    browser.visit('/timeline')

    assert browser.is_text_present("Noch keine Aktivität")

    # anonymous
    other = browser.clone()
    other.visit('/timeline')

    assert not other.is_text_present("Noch keine Aktivität")


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
    browser.find_by_name('photo').last.value = photo.name
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


def test_browse_directory_editor(browser, org_app):
    browser.login_admin()
    browser.visit('/directories/+new')

    assert browser.is_element_present_by_css('.formcode-toolbar', wait_time=5)

    browser.fill('title', "Restaurants")

    # add a title through the dropdown menu
    browser.find_by_css('.formcode-toolbar-element').click()
    browser.find_by_css('.formcode-snippet-name')[0].click()

    # add a text through the dropdown menu
    browser.find_by_css('.formcode-toolbar-element').click()
    browser.find_by_css('.formcode-snippet-name')[1].mouse_over()
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
    browser.find_by_value("Absenden").click()
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
            'enable_map': True
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
