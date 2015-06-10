from onegov.form import FormCollection
from webob.multidict import MultiDict


def test_has_submissions(session):
    collection = FormCollection(session)
    form = collection.definitions.add('Newsletter', definition="E-Mail = @@@")

    assert not form.has_submissions()

    data = MultiDict([
        ('e_mail', 'test@example.org'),
    ])

    collection.submissions.add(
        'newsletter', form.form_class(data), state='complete')

    assert not form.has_submissions(with_state='pending')
    assert form.has_submissions(with_state='complete')
    assert form.has_submissions()
