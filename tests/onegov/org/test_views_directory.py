from __future__ import annotations

import os
import re
import pytest
import transaction

from datetime import timedelta, datetime
from io import BytesIO
from onegov.core.utils import module_path
from onegov.file import FileCollection
from onegov.directory import (
    Directory, DirectoryEntry, DirectoryCollection,
    DirectoryConfiguration, DirectoryZipArchive)
from onegov.directory.errors import DuplicateEntryError
from onegov.directory.models.directory import DirectoryFile
from onegov.form import FormFile, FormSubmission
from onegov.form.display import TimezoneDateTimeFieldRenderer
from onegov.org.models import ExtendedDirectoryEntry
from purl import URL
from pytz import UTC
from textwrap import dedent
from sedate import standardize_date, utcnow, to_timezone, replace_timezone
from tests.shared.utils import (
    create_image, get_meta, extract_filename_from_response)
from webtest import Upload

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from onegov.org.models import ExtendedDirectory
    from sedate.types import TzInfoOrName
    from sqlalchemy.orm import Query
    from tests.shared.client import ExtendedResponse
    from tests.shared.postgresql import Postgresql
    from .conftest import Client


def dt_for_form(dt: datetime) -> str:
    """2020-11-25 12:29, using the correct format for local datetime
     fields """
    return dt.strftime('%Y-%m-%dT%H:%M')


def dt_repr(dt: datetime) -> str:
    return dt.strftime(TimezoneDateTimeFieldRenderer.date_format)


def dir_query(client: Client) -> Query[ExtendedDirectoryEntry]:
    return client.app.session().query(ExtendedDirectoryEntry)


def strip_s(dt: datetime, timezone: TzInfoOrName | None = None) -> datetime:
    """Strips the time from seconds ms and seconds according to inputs of
    type datetime-local """
    dt = datetime(
        dt.year, dt.month, dt.day, dt.hour, dt.minute)
    if not timezone:
        return dt
    return standardize_date(dt, timezone)


def create_directory(
    client: Client,
    publication: bool = True,
    required_publication: bool = False,
    change_reqs: bool = True,
    submission: bool = True,
    extended_submitter: bool = False,
    title: str = 'Meetings',
    lead: str | None = None,
    text: str | None = None
) -> ExtendedResponse:

    client.login_admin()
    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = title
    if lead:
        page.form['lead'] = lead
    if text:
        page.form['text'] = text
    page.form['structure'] = """
                    Name *= ___
                    Pic *= *.jpg|*.png|*.gif
                """
    page.form['content_fields'] = 'Name\nPic'
    page.form['content_hide_labels'] = 'Pic'
    page.form['title_format'] = '[Name]'
    page.form['enable_map'] = 'entry'
    page.form['thumbnail'] = 'Pic'
    page.form['enable_publication'] = publication
    page.form['required_publication'] = required_publication
    page.form['enable_change_requests'] = change_reqs
    if submission:
        page.form['enable_submissions'] = True

    if extended_submitter:
        page.form['submitter_meta_fields'] = [
            'submitter_name', 'submitter_address'
        ]

    meetings = page.form.submit().follow()
    return meetings


def accept_latest_submission(client: Client) -> ExtendedResponse:
    page = client.get('/tickets/ALL/open').click(
        "Annehmen", index=0).follow()
    accept_url = page.pyquery('.accept-link').attr('ic-post-to')
    client.post(accept_url)
    return page


def test_publication_added_by_admin(client: Client) -> None:
    utc_now = utcnow()
    now = to_timezone(utc_now, 'Europe/Zurich')

    meetings = create_directory(
        client, publication=False,
        lead='Meetings Directory'
    )

    # These url should be available for people who know it
    client.get('/directories/meetings/+submit')

    # create one entry as admin, publications is still available for admin
    page = meetings.click('Eintrag', index=0)
    page.form['name'] = 'Annual'
    page.form['pic'] = Upload('annual.jpg', create_image().read())
    page.form['publication_start'] = dt_for_form(now)
    page.form['publication_end'] = dt_for_form(now - timedelta(days=1))
    page = page.form.submit()
    assert 'Das Publikationsende muss in der Zukunft liegen' in page
    # we have to submit the file again, can't evade that
    page.form['pic'] = Upload('annual.jpg', create_image().read())
    annual_end = now + timedelta(days=1)
    page.form['publication_end'] = dt_for_form(annual_end)
    entry = page.form.submit().follow()

    # Check open graph meta tags
    assert get_meta(entry, 'og:description') == "Meetings Directory"
    assert get_meta(entry, 'og:image')
    assert get_meta(entry, 'og:image:width') == '50'
    assert get_meta(entry, 'og:image:height') == '50'
    assert get_meta(entry, 'og:image:alt') == 'annual.jpg'
    assert get_meta(entry, 'og:image:type') == 'image/png'

    # check that the change request url is not protected
    client.get('/directories/meetings/annual/change-request')

    assert 'Pic' not in entry

    entry_db = dir_query(client).one()
    assert entry_db.publication_end is not None
    # timezone unaware and not converted to utc before
    # contains publications relevant info
    assert entry_db.publication_end.tzinfo == UTC

    # check change request publication start deactivated
    page = entry.click('Änderung vorschlagen')
    assert 'publication_start' not in page.form.fields
    # check new submission
    page = meetings.click('Eintrag', index=1)
    assert 'publication_start' not in page.form.fields


def test_required_publication(client: Client) -> None:
    utc_now = utcnow()
    now = to_timezone(utc_now, 'Europe/Zurich')

    meetings = create_directory(client, required_publication=True)

    # These url should be available for people who know it
    client.get('/directories/meetings/+submit')

    # create one entry as admin, publications is still available for admin
    page = meetings.click('Eintrag', index=0)
    page.form['name'] = 'Annual'
    page.form['pic'] = Upload('annual.jpg', create_image().read())
    page.form['publication_start'] = dt_for_form(now)
    page = page.form.submit()
    assert 'Dieses Feld wird benötigt' in page
    # we have to submit the file again, can't evade that
    page.form['pic'] = Upload('annual.jpg', create_image().read())
    annual_end = now + timedelta(days=1)
    page.form['publication_end'] = dt_for_form(annual_end)
    page.form.submit().follow()


def test_publication_with_submission(client: Client) -> None:
    utc_now = utcnow()
    now = to_timezone(utc_now, 'Europe/Zurich')
    meetings = create_directory(
        client, publication=True, extended_submitter=True)

    # create a submission
    subm_page = meetings.click('Eintrag', index=1)
    subm_page.form['name'] = 'Monthly'
    subm_page.form['pic'] = Upload('monthly.jpg', create_image().read())
    subm_page.form['submitter'] = 'user@example.org'
    subm_page.form['submitter_name'] = 'User Example'
    subm_page.form['submitter_address'] = 'Testaddress'
    assert 'submitter_phone' not in subm_page.form.fields

    subm_page.form['publication_end'] = dt_for_form(now)
    subm_page = subm_page.form.submit()
    assert 'Das Publikationsende muss in der Zukunft liegen' in subm_page
    subm_page.form['pic'] = Upload('monthly.jpg', create_image().read())
    assert subm_page.form['publication_end'].value

    monthly_end = now + timedelta(minutes=2)
    subm_page.form['publication_end'] = dt_for_form(monthly_end)
    preview = subm_page.form.submit().follow()
    submission = client.app.session().query(FormSubmission).one()
    assert 'publication_end' in submission.data
    assert submission.submitter_name
    assert submission.submitter_address
    assert not submission.submitter_phone

    # is visible in the preview like coordinates
    assert 'Publikation' in preview
    assert dt_repr(monthly_end) in preview

    edit = preview.click('Bearbeiten')
    assert edit.form['publication_end'].value
    assert 'submitter_name' not in edit.form.fields

    preview.form.submit().follow()

    submission = client.app.session().query(FormSubmission).one()
    assert 'publication_end' in submission.data
    assert submission.submitter_name
    assert submission.submitter_address
    assert not submission.submitter_phone

    # Accept the new submission and test the ticket page
    ticket_page = accept_latest_submission(client)
    assert 'User Example' in ticket_page
    assert 'Testaddress' in ticket_page

    monthly_entry = dir_query(client).one()
    assert monthly_entry.name == 'monthly'
    assert not monthly_entry.publication_start
    assert monthly_entry.publication_end == strip_s(
        monthly_end, timezone='Europe/Zurich')

    assert monthly_entry.publication_started
    assert not monthly_entry.publication_ended
    assert monthly_entry.published

    meetings = client.get(meetings.request.url)
    assert 'Monthly' in meetings


def test_directory_publication_change_request(client: Client) -> None:
    utc_now = utcnow()
    now = to_timezone(utc_now, 'Europe/Zurich')
    meetings = create_directory(
        client, publication=True, extended_submitter=True)
    end = now + timedelta(days=1)

    # create entry
    page = meetings.click('Eintrag', index=0)
    page.form['name'] = 'Annual'
    page.form['pic'] = Upload('annual.jpg', create_image().read())
    page.form['publication_start'] = dt_for_form(now)
    page.form['publication_end'] = dt_for_form(end)
    entry = page.form.submit().follow()

    # make change requests
    anonymous = client.spawn()
    entry = anonymous.get(entry.request.url)
    page = entry.click('Änderung vorschlagen')
    page.form['submitter'] = 'user@example.org'
    page.form['submitter_name'] = 'User Example'
    page.form['submitter_address'] = 'User Address'
    assert page.form['publication_start'].value == dt_for_form(now)
    assert page.form['publication_end'].value == dt_for_form(
        now + timedelta(days=1))
    form_preview = page.form.submit().follow()
    assert 'Bitte geben Sie mindestens eine Änderung ein' in form_preview
    new_end = now + timedelta(days=9, minutes=5)
    form_preview.form['publication_end'] = dt_for_form(new_end)
    changes = form_preview.form.submit()
    assert changes.pyquery('.diff ins')[0].text == (
           dt_repr(replace_timezone(new_end, 'CET')))
    assert changes.pyquery('.diff del')[0].text == (
           dt_repr(standardize_date(end, 'UTC')))

    page = changes.form.submit().follow()

    supporter = client.spawn()
    supporter.login_supporter()
    ticket_page = accept_latest_submission(supporter)
    assert 'User Example' in ticket_page
    assert 'User Address' in ticket_page
    annual_entry = dir_query(client).first()
    assert annual_entry is not None
    assert annual_entry.name == 'annual'
    assert annual_entry.publication_end == (
           strip_s(new_end, timezone='Europe/Zurich'))
    assert annual_entry.publication_start == (
           strip_s(now, timezone='Europe/Zurich'))


def test_directory_change_requests(client: Client) -> None:
    client.login_admin()

    # create a directory that accepts change requests
    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Playgrounds"
    page.form['structure'] = """
        Name *= ___
        Pic *= *.jpg|*.png|*.gif
    """
    # We test as if change requests would be enabled
    page.form['enable_change_requests'] = False
    page.form['title_format'] = '[Name]'
    page.form['content_fields'] = 'Name\nPic'
    page = page.form.submit().follow()

    # create an entry
    page = page.click('Eintrag', index=0)
    page.form['name'] = 'Central Park'
    page.form['pic'] = Upload('test.jpg', create_image().read())
    assert 'publication_start' in page.form.fields
    page = page.form.submit().follow()
    img_url = page.pyquery('.field-display img').attr('href')

    # ask for a change, completely empty
    anonymous = client.spawn()
    page = anonymous.get(f'{page.request.url}/change-request')
    page.form['submitter'] = 'user@example.org'
    assert len(os.listdir(client.app.maildir)) == 0
    assert 'publication_start' not in page.form.fields
    form_preview = page.form.submit().follow()
    assert 'Bitte geben Sie mindestens eine Änderung ein' in form_preview
    form_preview.form['comment'] = 'This is better'
    form_preview.form['name'] = 'Diana Ross Playground'
    page = form_preview.form.submit().form.submit().follow()

    # check the ticket
    supporter = client.spawn()
    supporter.login_supporter()
    assert len(os.listdir(client.app.maildir)) == 1
    page = supporter.get('/tickets/ALL/open').click("Annehmen").follow()
    assert '<del>Central Park</del><ins>Diana Ross Playground</ins>' in page
    assert 'This is better' in page

    # make sure it hasn't been applied yet
    assert 'Central Park' in client.get(
        '/directories/playgrounds/central-park')

    # apply the changes
    page.click("Übernehmen")
    # User gets confirmation email
    assert len(os.listdir(client.app.maildir)) == 2
    page = supporter.get(page.request.url)
    assert 'Central Park' not in page
    assert 'Diana Ross Playground' in page
    assert 'This is better' in page

    # check if they were applied (the id won't have changed)
    page = client.get('/directories/playgrounds/central-park')
    assert 'Diana Ross Playground' in page
    # ensure the picture was not deleted
    assert page.pyquery('.field-display img').attr('href') == img_url


def test_directory_submissions(
    client: Client,
    postgres: Postgresql
) -> None:
    client.login_admin()

    # create a directory does not accept submissions
    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Points of Interest"
    page.form['structure'] = """
        Name *= ___
        Description = ...
        File = *.txt|*.csv
    """
    page.form['enable_submissions'] = False
    page.form['title_format'] = '[Name]'
    page.form['price'] = 'paid'
    page.form['price_per_submission'] = 100
    page.form['payment_method'] = 'manual'
    page = page.form.submit().follow()
    anon = client.spawn()
    assert "Eintrag vorschlagen" not in anon.get(page.request.url)

    # change it to accept submissions
    config_page = page.click("Konfigurieren")
    config_page.form['enable_submissions'] = True
    page = config_page.form.submit()

    # this fails because there are invisible fields
    assert "«Description» nicht sichtbar" in page
    page.form['lead_format'] = '[Description]'
    page.form['content_fields'] = "Name\nDescription\nFile"
    page = page.form.submit().follow()

    assert "Eintrag vorschlagen" in page

    # change it back to no submission and test if it works if the url is known
    config_page.form['enable_submissions'] = False
    config_page.form.submit()

    # create a submission with a missing field
    page = client.get('/directories/points-of-interest/+submit')
    page.form['description'] = '\n'.join((
        "The Washington Monument is an obelisk on the National Mall in",
        "Washington, D.C., built to commemorate George Washington, once",
        "commander-in-chief of the Continental Army and the first President",
        "of the United States",
    ))
    page.form['submitter'] = 'info@example.org'
    page = page.form.submit()

    assert "error" in page
    assert len(os.listdir(client.app.maildir)) == 0

    # add the missing field
    page.form['name'] = 'Washingtom Monument'

    page.form['file'] = Upload('README.txt', b'content.')
    page = page.form.submit().follow()

    # check the result
    assert "error" not in page
    assert "100.00" in page
    assert "Washingtom Monument" in page
    assert "George Washington" in page
    assert "README" in page

    # fix the result
    page = page.click("Bearbeiten", index=1)
    page.form['name'] = "Washington Monument"
    page = page.form.submit()

    assert "Washingtom Monument" not in page
    page = page.form.submit().follow()

    assert "DIR-" in page
    assert len(os.listdir(client.app.maildir)) == 1

    # the submission has not yet resulted in an entry
    assert 'Washington' not in client.get('/directories/points-of-interest')

    # adopt the submission through the ticket
    page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    assert "Offen" in page
    assert "100.00" in page
    assert "Übernehmen" in page
    assert "info@example.org" in page
    assert "Washington" in page
    assert "National Mall" in page
    assert "README" in page

    # if we adopt it it'll show up
    postgres.save()
    ticket_url = page.request.url
    accept_url = page.pyquery('.accept-link').attr('ic-post-to')
    client.post(accept_url)
    poi = client.get('/directories/points-of-interest')
    assert 'Washington' in poi
    assert len(os.listdir(client.app.maildir)) == 2

    entry = poi.click('Washington')
    # Check open graph meta tags, this time the file is not an image
    assert not get_meta(entry, "og:image")
    # When accepting the the entry, add a directory file with same reference
    formfile = client.app.session().query(FormFile).one()
    dirfile = client.app.session().query(DirectoryFile).one()
    assert formfile.reference == dirfile.reference

    # the description here is a multiline field
    desc = client.app.session().query(DirectoryEntry) \
        .one().values['description']

    assert '\n' in desc
    transaction.abort()

    # if we don't, it won't
    postgres.undo(pop=False)
    client.post(page.pyquery('.delete-link').attr('ic-post-to'))
    assert 'Washington' not in client.get('/directories/points-of-interest')

    # if the structure changes we might not be able to accept the submission
    postgres.undo(pop=False)
    page = client.get('/directories/points-of-interest').click('Konfigurieren')
    page.form['structure'] = """
        Name *= ___
        Description = ...
        File = *.txt|*.csv
        Category *= ___
    """
    page.form['lead_format'] = '[Description] [Category]'
    page.form.submit().follow()

    client.post(accept_url)

    page = client.get(ticket_url)
    assert "Der Eintrag ist nicht gültig" in page

    # in which case we can edit the submission to get it up to snuff
    page = page.click("Details bearbeiten")
    page.form['category'] = 'Monument'
    page.form.submit().follow()

    client.post(accept_url)

    page = client.get(ticket_url)
    assert 'Washington' in client.get('/directories/points-of-interest')

    # another way this can fail is with duplicate entries of the same name
    postgres.undo(pop=False)
    page = client.get('/directories/points-of-interest').click(
        'Eintrag', index=0)

    page.form['name'] = 'Washington Monument'
    page.form.submit()

    client.post(accept_url)

    page = client.get(ticket_url)
    assert "Ein Eintrag mit diesem Namen existiert bereits" in page

    # less severe structural changes are automatically applied
    postgres.undo(pop=False)
    page = client.get('/directories/points-of-interest').click('Konfigurieren')
    page.form['structure'] = """
        Name *= ___
        Description = ___
    """
    page.form.submit()

    client.post(accept_url)

    # the description here is no longer a multiline field
    desc = client.app.session().query(DirectoryEntry) \
        .one().values['description']

    assert '\n' not in desc
    transaction.abort()


def test_directory_visibility(client: Client) -> None:
    client.login_admin()

    page = client.get('/directories')
    assert 'Noch keine Verzeichnisse' in page

    page = page.click('Verzeichnis')
    page.form['title'] = "Clubs"
    page.form['lead'] = 'The famous club directory'
    page.form['structure'] = """
        Name *= ___
    """
    page.form['title_format'] = '[Name]'

    assert page.form['order_direction'].value == 'asc'
    page.form['order_direction'] = 'desc'
    page.form.submit()

    page = client.get('/directories/clubs')
    assert len(page.pyquery('.publication-nav a')) == 3
    page = page.click('Eintrag', index=0)
    page.form['name'] = 'Soccer Club'
    page.form.submit()

    anon = client.spawn()
    assert "Clubs" in anon.get('/directories')
    page = anon.get('/directories/clubs')
    assert "Soccer" in page
    assert 'The famous club directory' in page
    assert "Soccer" in anon.get('/directories/clubs/soccer-club')
    assert not page.pyquery('.publication-nav')

    page = client.get('/directories/clubs/soccer-club').click("Bearbeiten")
    page.form['access'] = 'private'
    page.form.submit()

    assert "Clubs" in anon.get('/directories')
    assert "Soccer" not in anon.get('/directories/clubs')
    assert anon.get('/directories/clubs/soccer-club', status=403)

    page = client.get('/directories/clubs/soccer-club').click("Bearbeiten")
    page.form['access'] = 'public'
    page.form.submit()

    page = client.get('/directories/clubs').click("Konfigurieren")
    page.form['access'] = 'private'
    assert page.form['order_direction'].value == 'desc'
    page.form.submit()

    assert "Clubs" not in anon.get('/directories')
    assert anon.get('/directories/clubs', status=403)
    assert anon.get('/directories/clubs/soccer-club')

    page = client.get('/directories/clubs').click("Konfigurieren")
    page.form['access'] = 'public'
    page.form.submit()

    transaction.begin()
    session = client.app.session()
    entry = session.query(ExtendedDirectoryEntry).one()
    entry.publication_end = (utcnow() - timedelta(minutes=5))
    session.flush()
    transaction.commit()

    # tests the links in the view as well
    page = client.get('/directories').click('Clubs')
    assert "Soccer" in page
    assert 'published_only=0' in page.request.url

    page = anon.get('/directories').click('Clubs')
    assert "Soccer" not in page
    assert 'published_only=1' in page.request.url
    # tests that we still trigger published_only to hide the entry
    # not adding the url kwarg
    page = anon.get('/directories/clubs')
    assert 'Soccer' not in page
    assert not page.pyquery('.publication-nav')

    editor = client.spawn()
    editor.login_editor()
    page = editor.get('/directories').click('Clubs')
    assert len(page.pyquery('.publication-nav a')) == 3


def test_markdown_in_directories(client: Client) -> None:
    client.login_admin()

    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Clubs"
    page.form['structure'] = """
        Name *= ___
        Notes = <markdown>
    """
    page.form['title_format'] = '[Name]'
    page.form['content_fields'] = 'Notes'
    page.form.submit().follow()

    page = client.get('/directories/clubs')
    page = page.click('Eintrag', index=0)
    page.form['name'] = 'Soccer Club'
    page.form['notes'] = '* Soccer rules!'
    page.form.submit().follow()

    assert "<li>Soccer rules" in client.get('/directories/clubs/soccer-club')


def test_bug_semicolons_in_choices_with_filters(client: Client) -> None:
    session = client.app.session()
    test_label = "Z: with semicolon"

    structure = f"""
    Name *= ___
    Choice *=
        (x) {test_label}
        ( ) B
        ( ) C
    """
    DirectoryCollection(session, type='extended').add(
        title='Choices',
        structure=structure,
        configuration=DirectoryConfiguration(
            title="[Name]",
            order=["Name"],
            display={
                'content': ['Name', 'Choice'],
                'contact': []
            },
            keywords=['Choice']
        )
    )
    session.flush()
    transaction.commit()
    client.login_admin()
    page = client.get('/directories/choices')
    # Test the counter for the filters
    assert f'{test_label}' not in page  # not shows as it has no entries

    page = page.click('Eintrag', index=0)
    page.form['name'] = '1'
    page = page.form.submit().follow()
    assert 'Ein neuer Verzeichniseintrag wurde hinzugefügt' in page

    page = client.get('/directories/choices')
    assert f'{test_label} (1)' in page

    page = page.click('Eintrag')
    page.form['name'] = '3'
    page.form['choice'] = 'C'
    page = page.form.submit().follow()
    assert 'Ein neuer Verzeichniseintrag wurde hinzugefügt' in page

    page = client.get('/directories/choices')
    assert 'C (1)' in page

    page = page.click('Eintrag')
    page.form['name'] = '2'
    page.form['choice'] = 'B'
    page = page.form.submit().follow()
    assert 'Ein neuer Verzeichniseintrag wurde hinzugefügt' in page

    page = client.get('/directories/choices')
    assert 'B (1)' in page

    # Get the url with the filter
    url = page.pyquery('.blank-label > a')[0].attrib['href']
    page = client.get(url)
    assert 'Choices' in page

    # Test that ordering is as defined by form and not alphabetically
    tags = page.pyquery('ul.tags a')
    assert [t.text for t in tags] == [f'{test_label} (1)', 'B (1)', 'C (1)']


def test_directory_export(client: Client) -> None:
    session = client.app.session()
    directories: DirectoryCollection[ExtendedDirectory]
    directories = DirectoryCollection(session, type='extended')
    dir_structure = """
                Name *= ___
                Contact (for infos) = ___
                Category =
                    [ ] A
                    [ ] B
                    [ ] Z: with semicolon
                Choice =
                    (x) yes
                    ( ) no
            """

    events = directories.add(
        title="Events",
        lead="The town's events",
        structure=dir_structure,
        configuration=DirectoryConfiguration(
            title="[name]",
            order=['name'],
            keywords=['Category', 'Choice']
        ),
        meta={
            'enable_map': False,
            'enable_submission': False,
            'enable_change_requests': False,
            'payment_method': None,
        },
        content={
            'marker_color': 'red',

        }
    )

    events.add(values=dict(
        name="Dance",
        contact_for_infos_='John',
        category=['A'],
        choice='yes'
    ))
    events.add(values=dict(
        name="Zumba",
        contact_for_infos_='Helen',
        category=['Z: with semicolon', 'B'],
        choice='no'
    ))
    transaction.commit()

    events = directories.by_name('events')  # type: ignore[assignment]
    assert events is not None
    export_page = client.get('/directories/events/+export')

    # Does not find A (1) link by its text otherwise
    filtered_url = export_page.pyquery(
        '.filter-panel a:first-of-type')[0].attrib['href']

    export_page = client.get(filtered_url)
    export_page.form['file_format'] = 'csv'
    export_view = export_page.form.submit()
    export_view_url = export_view.headers['location']
    assert URL(export_page.request.url).query_param('keywords') == \
           (URL(export_view_url).query_param('keywords') or None)

    resp = export_view.follow()
    filename = extract_filename_from_response(resp)
    assert filename is not None
    assert '.zip' in filename

    archive = DirectoryZipArchive.from_buffer(BytesIO(resp.body))

    count = 0

    def count_entry(entry: object) -> None:
        nonlocal count
        count += 1

    # create a directory in memory
    directory = archive.read(after_import=count_entry)
    assert directory != events
    assert count == 1
    assert directory.meta == events.meta


def test_add_directory_entries_with_duplicate_names(client: Client) -> None:
    client.login_admin()
    duplicate_name = "duplicate"

    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Playgrounds"
    page.form['structure'] = """
        Name *= ___
    """
    page.form['title_format'] = '[Name]'
    page.form.submit()

    page = client.get('/directories/playgrounds').click("^Eintrag$")
    page.form['name'] = duplicate_name
    page.form.submit()

    client.get('/directories/playgrounds').click("^Eintrag$")
    page.form['name'] = duplicate_name
    try:
        page = page.form.submit().follow()
        assert f'Der Eintrag {duplicate_name} existiert zweimal' in page
    except DuplicateEntryError:
        pytest.fail(
            "DuplicateEntryError not handled upon inserting duplicate "
            "entries in /directories")


def test_directory_numbering(client: Client) -> None:
    client.login_admin()

    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Trainers"
    page.form['structure'] = """
        Name *= ___
        Number = 0..10
    """
    page.form['title_format'] = '[Name]'
    page.form['numbering'] = 'none'
    page.form.submit()

    page = client.get('/directories/trainers').click("^Eintrag$")
    page.form['name'] = 'Emily Larlham'
    page.form['number'] = 4
    page.form.submit()

    page = client.get('/directories/trainers').click("^Eintrag$")
    page.form['name'] = 'Zak George'
    page.form['number'] = 5
    page.form.submit()

    page = client.get('/directories/trainers')
    numbers = page.pyquery('.entry-number')
    assert numbers == []

    page = page.click("Konfigurieren")
    page.form['numbering'] = 'standard'
    page.form.submit()

    page = client.get('/directories/trainers')
    numbers = page.pyquery('.entry-number')
    assert [t.text for t in numbers] == ['1. ', '2. ']

    page = page.click("Konfigurieren")
    page.form['numbering'] = 'custom'
    page.form['numbers'] = 'number'
    page.form.submit()

    page = client.get('/directories/trainers')
    numbers = page.pyquery('.entry-number')
    assert [t.text for t in numbers] == ['4. ', '5. ']


def test_directory_explicitly_link_referenced_files(client: Client) -> None:
    client.login_admin()

    path = module_path('tests.onegov.org', 'fixtures/sample.pdf')
    with open(path, 'rb') as f:
        page = client.get('/files')
        page.form['file'] = [Upload('Sample.pdf', f.read(), 'application/pdf')]
        page.form.submit()

    pdf_url = (
        client.get('/files')
        .pyquery('[ic-trigger-from="#button-1"]')
        .attr('ic-get-from')
        .removesuffix('/details')
    )
    pdf_link = f'<a href="{pdf_url}">Sample.pdf</a>'

    create_directory(client, text=pdf_link)

    session = client.app.session()
    pdf = FileCollection(session).query().one()
    directory = (
        DirectoryCollection(session).query()
        .filter(Directory.title == 'Meetings').one()
    )
    assert directory.files == [pdf]
    assert pdf.access == 'public'

    directory.access = 'mtan'  # type: ignore[attr-defined]
    session.flush()
    assert pdf.access == 'mtan'

    # link removed
    directory.files = []
    session.flush()
    assert pdf.access == 'secret'


def test_newline_in_directory_header(client: Client) -> None:

    client.login_admin()
    page = client.get('/directories')
    page = page.click('Verzeichnis')
    page.form['title'] = "Clubs"
    page.form['lead'] = 'this is a multiline\nlead'
    page.form['structure'] = """
        Name *= ___
    """
    page.form['title_format'] = '[Name]'
    page.form.submit()

    page = client.get('/directories/clubs')
    page = page.click('Eintrag', index=0)
    page.form['name'] = 'Soccer Club'
    page.form.submit()

    page = client.get('/directories/clubs')
    assert "this is a multiline<br>lead" in page


def test_change_directory_url(client: Client) -> None:
    client.login_admin()

    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Trainers"
    page.form['structure'] = """
        Name *= ___
    """
    page.form['title_format'] = '[Name]'
    page.form.submit()

    page = client.get('/directories/trainers/')

    change_dir_url = page.click('URL ändern')
    change_dir_url.form['name'] = 'sr'
    sr = change_dir_url.form.submit().follow()

    assert sr.request.url.endswith('/sr')

    # now attempt to change url to a directory url which already exists
    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Clubs"
    page.form['structure'] = """
        Name *= ___
    """
    page.form['title_format'] = '[Name]'
    page.form.submit()

    page = client.get('/directories/clubs/')
    change_dir_url = page.click('URL ändern')
    change_dir_url.form['name'] = 'clubs'

    page = change_dir_url.form.submit().maybe_follow()
    assert 'Das Formular enthält Fehler' in page


def test_directory_entry_subscription(client: Client) -> None:
    client.login_admin()

    assert len(os.listdir(client.app.maildir)) == 0

    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Trainers"
    page.form['structure'] = """
        Name *= ___
    """
    page.form['title_format'] = '[Name]'
    page.form['enable_update_notifications'] = True
    page = page.form.submit().follow()

    page = page.click('Benachrichtigungen bei neuen Einträgen erhalten')
    page.form['address'] = 'bliss@gmail.com'
    page = page.form.submit().follow()

    page = page.click('Benachrichtigungen bei neuen Einträgen erhalten')
    page.form['address'] = 'dream@gmail.com'
    page.form.submit().follow()

    assert len(os.listdir(client.app.maildir)) == 2
    message = client.get_email(0)['TextBody']
    confirm = re.search(r'Anmeldung bestätigen\]\(([^\)]+)', message).group(1)  # type: ignore[union-attr]
    message_2 = client.get_email(1)['TextBody']
    confirm_2 = re.search(  # type: ignore[union-attr]
        r'Anmeldung bestätigen\]\(([^\)]+)', message_2).group(1)

    illegal_confirm = confirm.split('/confirm')[0] + 'x/confirm'
    assert "falsches Token" in client.get(illegal_confirm).follow().follow()

    page = client.get(confirm).follow().follow()
    page = client.get(confirm).follow().follow()
    assert "bliss@gmail.com wurde erfolgreich" in page

    page = client.get(confirm_2).follow().follow()
    assert "dream@gmail.com wurde erfolgreich" in page

    page = client.get('/directories/trainers/+recipients')
    assert 'Zur Zeit sind 2 Abonnenten registriert' in page
    assert 'bliss@gmail.com' in page
    assert 'dream@gmail.com' in page

    page = client.get('/directories/trainers').click("^Eintrag$")
    page.form['name'] = 'Emily Larlham'
    page.form.submit()

    assert len(os.listdir(client.app.maildir)) == 3
    message = client.get_email(2)['TextBody']
    assert 'Emily Larlham' in message

    unsubscribe = re.search(r'abzumelden.\]\(([^\)]+)', message).group(1)  # type: ignore[union-attr]
    page = client.get(unsubscribe).follow().follow()
    assert "wurde erfolgreich abgemeldet" in page


def test_create_directory_accordion_layout(client: Client) -> None:

    def create_directory(client: Client, title: str) -> ExtendedResponse:
        page = (client.get('/directories').
                click('Verzeichnis'))
        page.form['title'] = title
        page.form['structure'] = "Question *= ___\nAnswer *= ___"
        page.form['title_format'] = '[Question]'
        page.form['layout'] = 'accordion'
        return page.form.submit().follow()

    client.login_admin()
    title = "Questions and Answers about smurfs"

    faq_dir = create_directory(client, title)
    assert title in faq_dir

    question = "Are smurfs real?"
    answer = "Yes, they are."
    q1 = faq_dir.click('Eintrag')
    q1.form['question'] = question
    q1.form['answer'] = answer
    q1 = q1.form.submit().follow()
    assert question in q1
    assert answer not in q1

    question = "Who is the boss of the smurfs?"
    q2 = faq_dir.click('Eintrag')
    q2.form['question'] = question
    q2.form['answer'] = 'Papa Schlumpf'
    q2 = q2.form.submit().follow()
    assert question in q2
    assert answer not in q2


def test_directory_migration(client: Client) -> None:
    # tests changing radio and checkbox options in directory structure

    client.login_admin()
    page = (client.get('/directories').click('Verzeichnis'))
    page.form['title'] = 'Order sweets'
    page.form['structure'] = dedent("""
        Nickname *= ___
        Do you want sweets? =
            (x) Yes
            ( ) No
        Choice =
            [ ] Gummi Bear
            [ ] Lolipop
    """)
    page.form['title_format'] = '[Nickname]'
    page = page.form.submit()
    assert not page.pyquery('.alert-box')

    page = client.get('/directories/order-sweets')
    page = page.click('Eintrag')
    page.form['nickname'] = 'Max'
    page.form['do_you_want_sweets_'] = 'Yes'
    page.form['choice'] = ['Lolipop', 'Gummi Bear']
    page = page.form.submit()
    assert not page.pyquery('.alert-box')

    # add options
    page = client.get('/directories/order-sweets').click('Konfigurieren')
    page.form['structure'] = dedent("""
        Nickname *= ___
        Do you want sweets? =
            (x) Yes
            ( ) No
            ( ) Not sure
        Choice =
            [ ] Donut
            [ ] Gummi Bear
            [ ] Chocolate
            [ ] Lolipop
            [ ] Ice cream
    """)
    page = page.form.submit()
    page.forms['main-form'].submit()  # confirm migration

    # rename multiple options
    page = client.get('/directories/order-sweets').click('Konfigurieren')
    page.form['structure'] = dedent("""
        Nickname *= ___
        Do you want sweets? =
            (x) Yes
            ( ) No
            ( ) Not sure
        Choice =
            [ ] Donut Hole
            [ ] Gummi Bears
            [ ] Chocolate
            [ ] Lolipop
            [ ] Ice cream
    """)
    page = page.form.submit()
    assert page.pyquery('.alert-box')
    assert 'Die verlangte Änderung kann nicht durchgeführt werden' in page
    assert 'Das Umbenennen mehrerer Optionen in derselben Migration wird nicht unterstützt' in page

    # rename single options
    page = client.get('/directories/order-sweets').click('Konfigurieren')
    page.form['structure'] = dedent("""
        Nickname *= ___
        Do you want sweets? =
            ( ) Yes
            ( ) No
            ( ) Not sure
        Choice =
            [ ] Donut Hole
            [ ] Gummi Bear
            [ ] Chocolate
            [ ] Lolipop
            [ ] Ice cream
    """)
    page = page.form.submit()
    page.forms['main-form'].submit()  # confirm migration

    # remove (selected) options
    page = client.get('/directories/order-sweets').click('Konfigurieren')
    page.form['structure'] = dedent("""
        Nickname *= ___
        Do you want sweets? =
            ( ) Yes
            ( ) No
            ( ) Not sure
        Choice =
            [ ] Donut Hole
            [ ] Chocolate
            [ ] Ice cream
    """)
    page = page.form.submit()
    page.forms['main-form'].submit()  # confirm migration

    # switch checkbox -> radio which is invalid
    page = client.get('/directories/order-sweets').click('Konfigurieren')
    page.form['structure'] = dedent("""
        Nickname *= ___
        Do you want sweets? =
            ( ) Yes
            ( ) Not sure
        Choice =
            ( ) Donut Hole
            ( ) Chocolate
            ( ) Ice cream
    """)
    page = page.form.submit()
    assert page.pyquery('.alert')
    assert 'Die verlangte Änderung kann nicht durchgeführt' in page
    assert ('Feld "Choice" kann nicht von Typ "checkbox" zu "radio" '
            'konvertiert werden') in page
