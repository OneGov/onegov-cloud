import pytest

from onegov.newsletter import NewsletterCollection, RecipientCollection
from onegov.newsletter.errors import AlreadyExistsError


def test_newsletter_collection(session):

    newsletters = NewsletterCollection(session)
    n = newsletters.add("My Newsletter", "<h1>My Newsletter</h1>")

    assert n.name == "my-newsletter"
    assert n.title == "My Newsletter"
    assert n.html == "<h1>My Newsletter</h1>"

    n = newsletters.by_name('my-newsletter')

    assert n.name == "my-newsletter"
    assert n.title == "My Newsletter"
    assert n.html == "<h1>My Newsletter</h1>"

    newsletters.delete(n)

    assert newsletters.by_name('my-newsletter') is None


def test_recipient_collection(session):

    recipients = RecipientCollection(session)
    r = recipients.add("info@example.org")

    assert r.address == "info@example.org"
    assert r.group is None

    r = recipients.by_id(r.id)

    assert r.address == "info@example.org"
    assert r.group is None

    r = recipients.by_address(r.address, 'abc')
    assert r is None

    r = recipients.by_address('info@example.org')

    assert r.address == "info@example.org"
    assert r.group is None

    recipients.delete(r)

    assert recipients.by_address('info@example.org') is None


def test_newsletter_already_exists(session):

    newsletters = NewsletterCollection(session)
    newsletters.add("My Newsletter", "<h1>My Newsletter</h1>")

    with pytest.raises(AlreadyExistsError) as e:
        newsletters.add("My Newsletter", "<h1>My Newsletter</h1>")

    assert e.value.args == ('my-newsletter', )
