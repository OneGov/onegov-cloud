import pytest

from datetime import datetime, timedelta
from io import BytesIO
from onegov.file import File
from onegov.form import CompleteFormSubmission
from onegov.form import FormCollection
from onegov.form import parse_form
from onegov.form import PendingFormSubmission
from onegov.form.errors import UnableToComplete
from onegov.form.utils import hash_definition
from sedate import utcnow
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError
from textwrap import dedent
from webob.multidict import MultiDict
from werkzeug.datastructures import FileMultiDict
from wtforms.csrf.core import CSRF


def test_form_checksum():
    assert hash_definition('abc') == '900150983cd24fb0d6963f7d28e17f72'


def test_add_form(session):
    collection = FormCollection(session)

    form = collection.definitions.add('Tax Form', definition=dedent("""
        First Name * = ___
        Last Name * = ___
    """))

    assert form.name == 'tax-form'
    assert form.form_class._source == form.definition

    form = collection.definitions.by_name('tax-form')

    assert form.name == 'tax-form'
    assert form.form_class._source == form.definition

    with pytest.raises(FlushError):
        form = collection.definitions.add('Tax Form', definition=dedent("""
            First Name * = ___
            Last Name * = ___
        """))

    assert form.checksum and form.checksum == hash_definition(form.definition)


def test_submit_form(session):
    collection = FormCollection(session)

    form = collection.definitions.add('TPS Report', definition=dedent("""
        First Name * = ___
        Last Name * = ___
        Date = YYYY.MM.DD
    """))

    data = MultiDict([
        ('first_name', 'Bill'),
        ('last_name', 'Lumbergh'),
        ('date', '2011-01-01')
    ])

    submitted_form = form.form_class(data)
    collection.submissions.add('tps-report', submitted_form, state='complete')

    form = collection.definitions.by_name('tps-report')
    submission = form.submissions[0]

    assert submission.checksum and submission.checksum == hash_definition(
        form.definition) == hash_definition(submission.definition)

    stored_form = submission.form_class(data=submission.data)

    assert submitted_form.data == stored_form.data


def test_submission_extra_data(session):
    collection = FormCollection(session)

    form = collection.definitions.add('TPS Report', definition=dedent("""
        First Name * = ___
        Last Name * = ___
        E-Mail = @@@
        Date = YYYY.MM.DD
    """))

    data = MultiDict([
        ('first_name', 'Bill'),
        ('last_name', 'Lumbergh'),
        ('e_mail', 'bill.lumbergh@initech.com'),
        ('date', '2011-01-01')
    ])

    submitted_form = form.form_class(data)
    submission = collection.submissions.add(
        'tps-report', submitted_form, state='complete')

    assert submission.title == 'Bill, Lumbergh'
    assert submission.email == 'bill.lumbergh@initech.com'


def test_definitions_with_submissions_count(session):
    collection = FormCollection(session)

    form = collection.definitions.add('Newsletter', definition="E-Mail = @@@")

    data = MultiDict([
        ('e_mail', 'test@example.org'),
    ])

    s1 = collection.submissions.add(
        'newsletter', form.form_class(data), state='complete')

    form = next(collection.get_definitions_with_submission_count())
    assert form.submissions_count == 1

    s2 = collection.submissions.add(
        'newsletter', form.form_class(data), state='complete')

    form = next(collection.get_definitions_with_submission_count())
    assert form.submissions_count == 2

    collection.submissions.delete(s1)

    form = next(collection.get_definitions_with_submission_count())
    assert form.submissions_count == 1

    collection.submissions.delete(s2)

    form = next(collection.get_definitions_with_submission_count())
    assert form.submissions_count == 0


def test_submit_pending(session):
    collection = FormCollection(session)

    form = collection.definitions.add('tweet', definition=dedent("""
        handle * = ___
        tweet * = ___[140]
    """))

    data = MultiDict([
        ('handle', '@href'),
        ('tweet', (
            "I think I found a way to tweet more than 140 characters! "
            "Finally I can tell my life's story in a single tweet. "
            "#hackersgonnahack #infosec #yolo"
        ))
    ])

    # pending forms may be submitted even if the are not valid
    submitted_form = form.form_class(data)
    assert not submitted_form.validate()

    submission = collection.submissions.add(
        'tweet', submitted_form, state='pending')
    assert isinstance(submission, PendingFormSubmission)

    assert 'handle' in submission.data
    assert 'tweet' in submission.data

    with pytest.raises(UnableToComplete):
        collection.submissions.complete_submission(submission)

    submission.data['tweet'] = "Nevermind, it didn't work #mybad"
    collection.submissions.complete_submission(submission)

    submission = collection.submissions.by_state('complete').first()
    submission.state == 'complete'
    submission.__class__ == CompleteFormSubmission


def test_remove_old_pending_submissions(session):
    collection = FormCollection(session)

    signup = collection.definitions.add('Signup', definition="E-Mail = @@@")

    data = MultiDict([('e_mail', 'info@example.org')])
    form = signup.form_class(data)

    collection.submissions.add('signup', form, state='complete')
    collection.submissions.add('signup', form, state='pending')

    assert collection.submissions.query().count() == 2

    collection.submissions.remove_old_pending_submissions(
        datetime.utcnow() - timedelta(hours=1))

    assert collection.submissions.query().count() == 2

    collection.submissions.remove_old_pending_submissions(
        datetime.utcnow() + timedelta(hours=1))

    assert collection.submissions.query().count() == 1


def test_no_store_csrf_token(session):
    collection = FormCollection(session)

    class MockCSRF(CSRF):

        def generate_csrf_token(self, csrf_token_field):
            return '0xdeadbeef'

    signup = collection.definitions.add('Signup', definition="E-Mail = @@@")

    data = MultiDict([
        ('e_mail', 'info@example.org'),
        ('csrf_token', '0xdeadbeef')
    ])

    form = signup.form_class(data, meta=dict(csrf=True, csrf_class=MockCSRF))
    submission = collection.submissions.add('signup', form, state='complete')

    assert 'e_mail' in submission.data
    assert 'csrf_token' not in submission.data


def test_delete_without_submissions(session):
    collection = FormCollection(session)

    form = collection.definitions.add('Newsletter', definition="E-Mail *= @@@")
    data = MultiDict([('e_mail', 'billg@microsoft.com')])

    collection.submissions.add(
        'newsletter', form.form_class(data), state='complete')

    with pytest.raises(IntegrityError):
        collection.definitions.delete('newsletter')


def test_delete_with_submissions(session):
    collection = FormCollection(session)

    form = collection.definitions.add('Newsletter', definition="E-Mail *= @@@")
    data = MultiDict([('e_mail', 'billg@microsoft.com')])

    collection.submissions.add(
        'newsletter', form.form_class(data), state='complete')
    collection.definitions.delete('newsletter', with_submissions=True)

    assert collection.submissions.query().count() == 0
    assert collection.definitions.query().count() == 0


def test_delete_with_pending_submissions(session):
    collection = FormCollection(session)

    form = collection.definitions.add('Newsletter', definition="E-Mail *= @@@")
    data = MultiDict([('e_mail', 'billg@microsoft.com')])

    collection.submissions.add(
        'newsletter', form.form_class(data), state='pending')
    collection.definitions.delete('newsletter', with_submissions=False)

    assert collection.submissions.query().count() == 0
    assert collection.definitions.query().count() == 0


def test_delete_fail_with_submissions(session):
    collection = FormCollection(session)

    form = collection.definitions.add('Newsletter', definition="E-Mail *= @@@")
    data = MultiDict([('e_mail', 'billg@microsoft.com')])

    collection.submissions.add(
        'newsletter', form.form_class(data), state='complete')

    with pytest.raises(IntegrityError):
        collection.definitions.delete('newsletter', with_submissions=False)


def test_file_submissions_update(session):
    collection = FormCollection(session)

    # upload a new file
    definition = collection.definitions.add('File', definition="File = *.txt")

    data = FileMultiDict()
    data.add_file('file', BytesIO(b'foobar'), filename='foobar.txt')

    submission = collection.submissions.add(
        'file', definition.form_class(data), state='pending')

    assert len(submission.files) == 1
    assert submission.files[0].checksum == '3858f62230ac3c915f300c664312c63f'

    # replace the existing file
    previous_file = submission.files[0]
    session.refresh(submission)

    data = FileMultiDict()
    data.add('file', 'replace')
    data.add_file('file', BytesIO(b'barfoo'), filename='foobar.txt')

    collection.submissions.update(submission, definition.form_class(data))
    session.flush()
    session.refresh(submission)

    assert len(submission.files) == 1
    assert previous_file.id != submission.files[0].id
    assert previous_file.checksum != submission.files[0].checksum

    # keep the file
    previous_file = submission.files[0]
    session.refresh(submission)

    data = FileMultiDict()
    data.add('file', 'keep')
    data.add_file('file', BytesIO(b''), filename='foobar.txt')

    collection.submissions.update(submission, definition.form_class(data))
    session.flush()
    session.refresh(submission)

    assert len(submission.files) == 1
    assert previous_file.id == submission.files[0].id
    assert previous_file.checksum == submission.files[0].checksum

    # delete the file
    session.refresh(submission)

    data = FileMultiDict()
    data.add('file', 'delete')
    data.add_file('file', BytesIO(b'asdf'), filename='foobar.txt')

    collection.submissions.update(submission, definition.form_class(data))
    assert len(submission.files) == 0


def test_file_submissions_cascade(session):

    collection = FormCollection(session)

    # upload a new file
    definition = collection.definitions.add('File', definition="File = *.txt")

    data = FileMultiDict()
    data.add_file('file', BytesIO(b'foobar'), filename='foobar.txt')

    collection.submissions.add(
        'file', definition.form_class(data), state='pending')

    assert session.query(File).count() == 1
    session.flush()

    collection.submissions.remove_old_pending_submissions(older_than=(
        datetime.utcnow() + timedelta(seconds=60)))

    session.flush()

    assert session.query(File).count() == 0


def test_get_current(session):
    collection = FormCollection(session)

    form = collection.definitions.add('Newsletter', definition="E-Mail *= @@@")
    data = MultiDict([('e_mail', 'billg@microsoft.com')])

    submission = collection.submissions.add(
        'newsletter', form.form_class(data), state='complete')

    submission.created = submission.modified = utcnow() - timedelta(days=1)

    assert not collection.submissions.by_id(submission.id, current_only=True)
    assert collection.submissions.by_id(submission.id, current_only=False)


def test_add_externally_defined_submission(session):
    collection = FormCollection(session)

    form_class = parse_form("E-Mail *= @@@")
    form = form_class(data={'e_mail': 'info@example.org'})

    submission = collection.submissions.add_external(form, state='pending')

    assert collection.definitions.query().count() == 0
    assert collection.submissions.query().count() == 1

    stored_form = submission.form_class(data=submission.data)

    assert stored_form.e_mail.data == 'info@example.org'
    assert stored_form.e_mail.data == form.e_mail.data

    # externally defined submission are not automatically removed
    date = datetime.utcnow() + timedelta(seconds=60)

    collection.submissions.remove_old_pending_submissions(older_than=date)
    assert collection.submissions.query().count() == 1

    collection.submissions.remove_old_pending_submissions(
        older_than=date, include_external=True)
    assert collection.submissions.query().count() == 0
