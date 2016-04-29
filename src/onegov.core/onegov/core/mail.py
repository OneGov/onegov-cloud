import mailthon.headers as headers
import os.path
import re

from email.mime.multipart import MIMEMultipart
from html2text import html2text
from mailbox import Maildir, MaildirMessage
from mailthon.enclosure import HTML, PlainText, Attachment
from mailthon.envelope import Envelope as BaseEnvelope
from mailthon.postman import Postman


VALID_PLAINTEXT_CHARACTERS = re.compile(r"""
    [
        \d  # decimals
        \w  # words
        \n  # new lines

        # emojis
        \U00002600-\U000027BF
        \U0001f300-\U0001f64F
        \U0001f680-\U0001f6FF
    ]+
""", re.VERBOSE)


def convert_to_plaintext(html):

    # filter out duplicated lines and lines without any text
    lines = html2text(html, '', bodywidth=0).splitlines()
    lines = (l.strip() for l in lines)
    lines = (l for l in lines if VALID_PLAINTEXT_CHARACTERS.search(l))

    # use double newlines to get paragraphs
    plaintext = '\n\n'.join(lines)

    # in an attempt to create proper markdown html2text will escape
    # dots. Since markdown is not something we care about here, we undo that
    plaintext = plaintext.replace('\\.', '.')

    return plaintext


def email(sender=None, receivers=(), cc=(), bcc=(),
          subject=None, content=None, encoding='utf8',
          attachments=()):
    """
    Creates an Envelope object with a HTML *content*, as well as a *plaintext*
    alternative generated from the HTML content.

    :param content: HTML content.
    :param encoding: Encoding of the email.
    :param attachments: List of filenames to
        attach to the email.

    Note: this is basically a copy of :func:`mailthon.api.email`, though it
    adds the plaintext alternative.
    """

    if content:
        # turn the html email into a plaintext representation
        # this leads to a lower spam rating
        plaintext = convert_to_plaintext(content)
    else:
        plaintext = None

    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred
    enclosure = [
        PlainText(plaintext, encoding),
        HTML(content, encoding),
    ]
    enclosure.extend(Attachment(k) for k in attachments)
    return Envelope(
        headers=[
            headers.subject(subject),
            headers.sender(sender),
            headers.to(*receivers),
            headers.cc(*cc),
            headers.bcc(*bcc),
            headers.date(),
            headers.message_id(),
        ],
        enclosure=enclosure,
    )


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
