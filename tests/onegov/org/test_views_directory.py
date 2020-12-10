from datetime import timedelta, datetime

import transaction
from pytz import UTC
from sedate import standardize_date, utcnow, to_timezone, replace_timezone
from webtest import Upload

from onegov.directory import DirectoryEntry
from onegov.directory.models.directory import DirectoryFile
from onegov.form import FormFile, FormSubmission
from onegov.form.display import TimezoneDateTimeFieldRenderer
from onegov.org.models import ExtendedDirectoryEntry
from tests.shared.utils import create_image, open_in_browser


def dt_for_form(dt):
    """2020-11-25 12:29:00"""
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def dt_repr(dt):
    return dt.strftime(TimezoneDateTimeFieldRenderer.date_format)


def dir_query(client):
    return client.app.session().query(ExtendedDirectoryEntry)


def strip_ms(dt, timezone=None):
    dt = datetime(
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    if not timezone:
        return dt
    return standardize_date(dt, timezone)


def create_directory(client, publication=True, change_reqs=True):
    client.login_admin()
    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Meetings"
    page.form['structure'] = """
                    Name *= ___
                    Pic *= *.jpg|*.png|*.gif
                """
    page.form['content_fields'] = 'Name\nPic'
    page.form['title_format'] = '[Name]'
    page.form['enable_map'] = 'entry'
    page.form['enable_publication'] = publication
    page.form['enable_change_requests'] = change_reqs
    page.form['enable_submissions'] = True
    meetings = page.form.submit().follow()
    return meetings


def accecpt_latest_submission(client):
    page = client.get('/tickets/ALL/open').click(
        "Annehmen", index=0).follow()
    accept_url = page.pyquery('.accept-link').attr('ic-post-to')
    client.post(accept_url)


def test_publication_added_by_admin(client):
    utc_now = utcnow()
    now = to_timezone(utc_now, 'Europe/Zurich')

    meetings = create_directory(client, publication=False)

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
    entry_db = dir_query(client).one()
    # timezone unaware and not converted to utc before
    # contains publications relevant info
    assert entry_db.publication_end.tzinfo == UTC

    # check change request publication start deactivated
    page = entry.click('Änderung vorschlagen')
    assert 'publication_start' not in page.form.fields
    # check new submission
    page = meetings.click('Eintrag', index=1)
    assert 'publication_start' not in page.form.fields


def test_publication_with_submission(client):
    utc_now = utcnow()
    now = to_timezone(utc_now, 'Europe/Zurich')
    meetings = create_directory(client, publication=True)

    # create a submission
    submission = meetings.click('Eintrag', index=1)
    submission.form['name'] = 'Monthly'
    submission.form['pic'] = Upload('monthly.jpg', create_image().read())
    submission.form['submitter'] = 'user@example.org'
    submission.form['publication_end'] = dt_for_form(now)
    submission = submission.form.submit()
    assert 'Das Publikationsende muss in der Zukunft liegen' in submission
    submission.form['pic'] = Upload('monthly.jpg', create_image().read())
    assert submission.form['publication_end'].value

    monthly_end = now + timedelta(minutes=2)
    submission.form['publication_end'] = dt_for_form(monthly_end)
    preview = submission.form.submit().follow()
    submission = client.app.session().query(FormSubmission).one()
    assert 'publication_end' in submission.data
    # is visible in the preview like coordinates
    assert 'Publikation' in preview
    assert dt_repr(monthly_end) in preview

    edit = preview.click('Bearbeiten')
    assert edit.form['publication_end'].value

    preview.form.submit().follow()

    submission = client.app.session().query(FormSubmission).one()
    assert 'publication_end' in submission.data

    # Accept the new submission
    accecpt_latest_submission(client)

    monthly_entry = dir_query(client).one()
    assert monthly_entry.name == 'monthly'
    assert not monthly_entry.publication_start
    assert monthly_entry.publication_end == strip_ms(
        monthly_end, timezone='Europe/Zurich')

    assert monthly_entry.publication_started
    assert not monthly_entry.publication_ended
    assert monthly_entry.published

    meetings = client.get(meetings.request.url)
    assert 'Monthly' in meetings


def test_directory_publication_change_request(client):
    utc_now = utcnow()
    now = to_timezone(utc_now, 'Europe/Zurich')
    meetings = create_directory(client, publication=True)
    end = now + timedelta(days=1)

    # create entry
    page = meetings.click('Eintrag', index=0)
    page.form['name'] = 'Annual'
    page.form['pic'] = Upload('annual.jpg', create_image().read())
    page.form['publication_start'] = dt_for_form(now)
    page.form['publication_end'] = dt_for_form(end)
    entry = page.form.submit().follow()

    # make change requests
    page = entry.click('Änderung vorschlagen')
    page.form['submitter'] = 'user@example.org'
    assert page.form['publication_start'].value == dt_for_form(now)
    assert page.form['publication_end'].value == dt_for_form(
        now + timedelta(days=1))
    form_preview = page.form.submit().follow()
    assert 'Bitte geben Sie mindestens eine Änderung ein' in form_preview
    new_end = now + timedelta(days=9, minutes=5)
    form_preview.form['publication_end'] = dt_for_form(new_end)
    changes = form_preview.form.submit()
    assert changes.pyquery('.diff ins')[0].text == dt_repr(replace_timezone(new_end, 'CET'))
    assert changes.pyquery('.diff del')[0].text == dt_repr(standardize_date(end, 'UTC'))

    page = changes.form.submit().follow()
    accecpt_latest_submission(client)
    annual_entry = dir_query(client).first()
    assert annual_entry.name == 'annual'
    assert annual_entry.publication_end == strip_ms(new_end, timezone='Europe/Zurich')
    assert annual_entry.publication_start == strip_ms(now, timezone='Europe/Zurich')


def test_directory_change_requests(client):

    client.login_admin()

    # create a directory that accepts change requests
    page = client.get('/directories').click('Verzeichnis')
    page.form['title'] = "Playgrounds"
    page.form['structure'] = """
        Name *= ___
        Pic *= *.jpg|*.png|*.gif
    """
    page.form['enable_change_requests'] = True
    page.form['title_format'] = '[Name]'
    page.form['content_fields'] = 'Name\nPic'
    page = page.form.submit().follow()

    # create an entry
    page = page.click('Eintrag')
    page.form['name'] = 'Central Park'
    page.form['pic'] = Upload('test.jpg', create_image().read())
    assert 'publication_start' in page.form.fields
    page = page.form.submit().follow()
    img_url = page.pyquery('.field-display img').attr('href')

    # ask for a change, completely empty
    page = page.click("Änderung vorschlagen")
    page.form['submitter'] = 'user@example.org'
    assert len(client.app.smtp.outbox) == 0
    assert 'publication_start' not in page.form.fields
    form_preview = page.form.submit().follow()
    assert 'Bitte geben Sie mindestens eine Änderung ein' in form_preview
    form_preview.form['comment'] = 'This is better'
    form_preview.form['name'] = 'Diana Ross Playground'
    page = form_preview.form.submit().form.submit().follow()

    # check the ticket
    assert len(client.app.smtp.outbox) == 1
    page = client.get('/tickets/ALL/open').click("Annehmen").follow()
    assert '<del>Central Park</del><ins>Diana Ross Playground</ins>' in page
    assert 'This is better' in page

    # make sure it hasn't been applied yet
    assert 'Central Park' in \
        client.get('/directories/playgrounds/central-park')

    # apply the changes
    page.click("Übernehmen")
    # User gets confirmation email
    assert len(client.app.smtp.outbox) == 2
    page = client.get(page.request.url)
    assert 'Central Park' not in page
    assert 'Diana Ross Playground' in page
    assert 'This is better' in page

    # check if they were applied (the id won't have changed)
    page = client.get('/directories/playgrounds/central-park')
    assert 'Diana Ross Playground' in page
    # ensure the picture was not deleted
    assert page.pyquery('.field-display img').attr('href') == img_url


def test_directory_submissions(client, postgres):

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
    assert "Eintrag vorschlagen" not in page

    # change it to accept submissions
    page = page.click("Konfigurieren")
    page.form['enable_submissions'] = True
    page = page.form.submit()

    # this fails because there are invisible fields
    assert "«Description» nicht sichtbar" in page
    page.form['lead_format'] = '[Description]'
    page.form['content_fields'] = "Name\nDescription\nFile"
    page = page.form.submit().follow()

    assert "Eintrag vorschlagen" in page

    # create a submission with a missing field
    page = page.click("Eintrag vorschlagen")
    page.form['description'] = '\n'.join((
        "The Washington Monument is an obelisk on the National Mall in",
        "Washington, D.C., built to commemorate George Washington, once",
        "commander-in-chief of the Continental Army and the first President",
        "of the United States",
    ))
    page.form['submitter'] = 'info@example.org'
    page = page.form.submit()

    assert "error" in page
    assert len(client.app.smtp.outbox) == 0

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
    assert len(client.app.smtp.outbox) == 1

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
    assert 'Washington' in client.get('/directories/points-of-interest')
    assert len(client.app.smtp.outbox) == 2

    # When accepting the the entry, add a directory file with same reference
    formfile = client.app.session().query(FormFile).one()
    dirfile = client.app.session().query(DirectoryFile).one()
    assert formfile.reference == dirfile.reference

    # the description here is a multiline field
    desc = client.app.session().query(DirectoryEntry)\
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
    desc = client.app.session().query(DirectoryEntry)\
        .one().values['description']

    assert '\n' not in desc
    transaction.abort()


def test_directory_visibility(client):

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
    page.form.submit()

    page = client.get('/directories/clubs')
    page = page.click('Eintrag', index=0)
    page.form['name'] = 'Soccer Club'
    page.form.submit()

    anon = client.spawn()
    assert "Clubs" in anon.get('/directories')
    page = anon.get('/directories/clubs')
    assert "Soccer" in page
    assert 'The famous club directory' in page
    assert "Soccer" in anon.get('/directories/clubs/soccer-club')

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

    assert "Soccer" in client.get('/directories/clubs')
    assert "Soccer" not in anon.get('/directories/clubs')
