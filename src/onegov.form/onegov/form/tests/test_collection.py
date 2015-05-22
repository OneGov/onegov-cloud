import pytest

from onegov.form import FormCollection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError
from textwrap import dedent
from webob.multidict import MultiDict


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
    collection.submissions.add('tps-report', submitted_form)

    form = collection.definitions.by_name('tps-report')
    submission = form.submissions[0]

    stored_form = submission.form_class(data=submission.data)

    assert submitted_form.data == stored_form.data


def test_delete_without_submissions(session):
    collection = FormCollection(session)

    form = collection.definitions.add('Newsletter', definition="E-Mail *= @@@")
    data = MultiDict([('e_mail', 'billg@microsoft.com')])

    collection.submissions.add('newsletter', form.form_class(data))

    with pytest.raises(IntegrityError):
        collection.definitions.delete('newsletter')


def test_delete_with_submissions(session):
    collection = FormCollection(session)

    form = collection.definitions.add('Newsletter', definition="E-Mail *= @@@")
    data = MultiDict([('e_mail', 'billg@microsoft.com')])

    collection.submissions.add('newsletter', form.form_class(data))
    collection.definitions.delete('newsletter', with_submissions=True)

    assert collection.submissions.query().count() == 0
    assert collection.definitions.query().count() == 0
