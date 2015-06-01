import pytest

from datetime import datetime, timedelta
from onegov.form import FormCollection, PendingFormSubmission
from onegov.form.errors import UnableToComplete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError
from textwrap import dedent
from webob.multidict import MultiDict
from wtforms.csrf.core import CSRF


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

    stored_form = submission.form_class(data=submission.data)

    assert submitted_form.data == stored_form.data


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

    # but invalid data is purged from the submission
    assert 'handle' in submission.data
    assert 'tweet' not in submission.data

    with pytest.raises(UnableToComplete):
        submission.complete()

    submission.data['tweet'] = "Nevermind, it didn't work #mybad"
    submission.complete()


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
