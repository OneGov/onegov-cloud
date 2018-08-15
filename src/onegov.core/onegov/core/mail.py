import mailthon.headers as headers
import os.path

from email.mime.multipart import MIMEMultipart
from mailbox import Maildir, MaildirMessage
from mailthon.enclosure import HTML, PlainText, Attachment, Enclosure
from mailthon.envelope import Envelope as BaseEnvelope
from mailthon.postman import Postman
from onegov.core.html import html_to_text


def email(sender=None, receivers=(), cc=(), bcc=(),
          subject=None, content=None, encoding='utf8',
          attachments=(), category='marketing', plaintext=None):
    """
    Creates an Envelope object with a HTML *content*, as well as a *plaintext*
    alternative generated from the HTML content.

    :param content: HTML content.
    :param encoding: Encoding of the email.
    :param attachments: Either a list of :class:`mailthon.enclosure.Enclosure`
        or a list of filenames to attach to the email.

    Note: this is basically a copy of :func:`mailthon.api.email`, though it
    adds the plaintext alternative.
    """

    if content and not plaintext:
        # turn the html email into a plaintext representation
        # this leads to a lower spam rating
        plaintext = html_to_text(content)

    headers_ = [
        headers.subject(subject),
        headers.sender(sender),
        headers.to(*receivers),
        headers.cc(*cc),
        headers.bcc(*bcc),
        headers.date(),
        headers.message_id(),
        ('X-Category', category),
    ]

    # According to RFC 2046, the last part of a multipart message, in this
    # case the HTML message, is best and preferred
    enclosure = [PlainText(plaintext, encoding), HTML(content, encoding)]

    if not attachments:
        # simple 'mime-multipart/alternative'
        envelope = Envelope(headers=headers_, enclosure=enclosure)
    else:
        # 'multipart/mixed' with 'mime-multipart/alternative' and attachments
        enclosure = [Envelope(headers=[], enclosure=enclosure)]
        enclosure.extend(
            k if isinstance(k, Enclosure) else Attachment(k)
            for k in attachments
        )
        envelope = BaseEnvelope(headers=headers_, enclosure=enclosure)

    return envelope


class Envelope(BaseEnvelope):
    """ Changes the mailthon envelope to use mime-multipart/alternative.

    """

    def mime(self):
        mime = MIMEMultipart('alternative')
        for item in self.enclosure:
            mime.attach(item.mime())
        self.headers.prepare(mime)
        return mime


class MaildirTransport(object):
    """ A transport that pretends to be like python's smtplib.SMTP transport,
    but actually just stores files into a maildir.

    """

    def __init__(self, host, port, maildir):
        # host and port exist for mailthon compatibility, they are ignored
        self.maildir = Maildir(maildir, create=True)

        for d in (os.path.join(maildir, d) for d in ('new', 'cur', 'tmp')):
            if not os.path.exists(d):
                os.makedirs(d)

    def sendmail(self, from_addr, to_addrs, message):
        self.maildir.add(MaildirMessage(message))

        return {}

    def noop(self):
        return 250, ""

    def ehlo(self):
        pass

    def quit(self):
        pass


class MaildirPostman(Postman):
    """ A mailthon postman that stores mails to a maildir. """
    transport = MaildirTransport
