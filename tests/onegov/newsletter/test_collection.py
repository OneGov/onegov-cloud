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
    r1 = recipients.add("info@example.org", confirmed=True)
    r2 = recipients.add("info@info.io", group='tech', confirmed=False)

    assert recipients.count() == 2
    assert r1.address == "info@example.org"
    assert r1.group is None
    assert r1.confirmed
    assert r2.address == "info@info.io"
    assert r2.group == 'tech'
    assert not r2.confirmed

    r1 = recipients.by_id(r1.id)

    assert r1.address == "info@example.org"
    assert r1.group is None

    assert recipients.by_id('abc') is None
    assert recipients.by_address(r1.address, 'abc') is None

    assert recipients.ordered_by_status_address().all() == [r2, r1]

    r1 = recipients.by_address('info@example.org')

    assert r1.address == "info@example.org"
    assert r1.group is None

    recipients.delete(r1)

    assert recipients.by_address('info@example.org') is None
    assert recipients.count() == 1

    recipients.delete(r2)
    assert recipients.count() == 0


def test_newsletter_already_exists(session):

    newsletters = NewsletterCollection(session)
    newsletters.add("My Newsletter", "<h1>My Newsletter</h1>")

    with pytest.raises(AlreadyExistsError) as e:
        newsletters.add("My Newsletter", "<h1>My Newsletter</h1>")

    assert e.value.args == ('my-newsletter', )
