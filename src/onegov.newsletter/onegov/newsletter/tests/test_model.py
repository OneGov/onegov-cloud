import pytest
import transaction

from onegov.newsletter import Newsletter, Recipient, Subscription
from onegov.newsletter.models import newsletter_recipients
from sqlalchemy.exc import IntegrityError


def test_recipients_unconfirmed(session):
    session.add(Recipient(address='info@example.org'))
    transaction.commit()

    assert session.query(Recipient).first().confirmed is False


def test_recipients_unique_per_group(session):

    for group in (None, 'foo', 'bar'):
        session.add(Recipient(address='info@example.org', group=group))
        transaction.commit()

        with pytest.raises(IntegrityError):
            session.add(Recipient(address='info@example.org', group=group))
            session.flush()

        transaction.abort()


def test_valid_name():
    with pytest.raises(AssertionError):
        Newsletter(
            title="Normalization Works",
            name="Or does it?",
            html="<h1>Normalization Works</h1>"
        )


def test_recipients_valid_email():
    with pytest.raises(AssertionError):
        Recipient(address="no-email")


def test_recipient_subscription(session):
    recipient = Recipient(address="info@example.org")
    session.add(recipient)
    session.flush()

    assert len(recipient.token) >= 64

    assert not recipient.confirmed
    assert not Subscription(recipient, 'asdf').confirm()
    assert not recipient.confirmed

    assert recipient.subscription.confirm()
    assert recipient.confirmed

    assert not Subscription(recipient, 'asdf').unsubscribe()
    assert recipient.confirmed

    assert recipient.subscription.unsubscribe()
    assert session.query(Recipient).count() == 0


def test_newsletter_recipients_cascade(session):

    # is the relationship reflected correctly?
    newsletter = Newsletter(
        title="10 things you didn't know",
        name="10-things-you-didnt-know",
        html="<h1>10 things you didn't know</h1>",
        recipients=[
            Recipient(address='info@example.org')
        ]
    )

    session.add(newsletter)
    transaction.commit()

    newsletter = session.query(Newsletter).first()
    recipient = session.query(Recipient).first()

    assert len(newsletter.recipients) == 1
    assert len(recipient.newsletters) == 1
    assert session.query(newsletter_recipients).count() == 1

    # is the delete cascaded if the newsletter is deleted?
    session.delete(newsletter)
    transaction.commit()

    recipient = session.query(Recipient).first()
    assert len(recipient.newsletters) == 0
    assert session.query(newsletter_recipients).count() == 0

    # is the delete cascaded if the recipient is deleted?
    recipient.newsletters.append(Newsletter(
        title="How Bitcoin is so 90s",
        name="how-bitcoin-is-so-90s",
        html="<h1>How Bitcoin is so 90s</h1>"
    ))
    transaction.commit()

    newsletter = session.query(Newsletter).first()
    session.delete(newsletter.recipients[0])
    transaction.commit()

    newsletter = session.query(Newsletter).first()
    assert len(newsletter.recipients) == 0
    assert session.query(newsletter_recipients).count() == 0
