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


def test_browse_directory_uploads(browser, org_app):
    DirectoryCollection(org_app.session(), type='extended').add(
        title="Crime Scenes",
        structure="""
            Name *= ___
            Description *= ...
            Photo = *.png|*.jpg
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

    assert not browser.is_element_present_by_css('.field-display img')
