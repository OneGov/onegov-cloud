import os.path
import magic

from base64 import b64encode
from email.utils import parseaddr, formataddr
from onegov.core.html import html_to_text


class Attachment:
    """
    Represents a mail attachment that can be passed to prepare_mail
    """

    # TODO: Add support for ContentID for embedded attachments.
    def __init__(self, filename, content=None, content_type=None):
        self.filename = os.path.basename(filename)
        if content is None:
            with open(filename, 'rb') as fd:
                content = fd.read()
        elif hasattr(content, 'read'):
            content = content.read()

        if isinstance(content, str):
            content = content.encode('utf-8')

        assert isinstance(content, bytes)
        self.content = content

        if content_type is None:
            # shortcut for depot.io.interfaces.StoredFile
            if hasattr(content, 'content_type'):
                content_type = content.content_type
            else:
                content_type = magic.from_buffer(self.content, mime=True)
        self.content_type = content_type

    def prepare(self):
        """
        Prepares attachment so it can be sent to Postmark API.
        """
        content = b64encode(self.content).decode('ascii')
        return {
            'Name': self.filename,
            'Content': content,
            'ContentType': self.content_type
        }


def prepare_email(sender, reply_to=None, receivers=(), cc=(), bcc=(),
                  subject=None, content=None, plaintext=None,
                  attachments=(), headers=None, stream='marketing'):
    """
    Creates a dictiornary that can be turned into JSON as is and sent
    to the Postmark API.

    :param content: HTML content.
    :param attachments: Either a list of :class:`onegov.core.email.Attachment`
        or a list of filenames/os.PathLike to attach to the email.
    :param headers: Dictionary containing additional headers to be set

    """

    # Postmark API limit
    assert len(receivers) <= 50

    if not plaintext:
        # if no plaintext is given we require content
        assert content

        # turn the html email into a plaintext representation
        # this leads to a lower spam rating
        plaintext = html_to_text(content)

    message = {
        'From': sender,
        'To': ', '.join(receivers),
        'TextBody': plaintext,
        'MessageStream': stream,
    }

    if reply_to is not None:
        message['ReplyTo'] = reply_to

        # if the reply to address has a name part (Name <address@host>), use
        # the name part for the sender address as well to somewhat hide the
        # fact that we're using a noreply email
        name, address = parseaddr(reply_to)

        if name and not parseaddr(sender)[0]:
            message['From'] = formataddr((name, sender))

    if cc:
        # Postmark API limit
        assert len(cc) <= 50
        message['Cc'] = ', '.join(cc)

    if bcc:
        # Postmark API limit
        assert len(bcc) <= 50
        message['Bcc'] = ', '.join(bcc)

    if subject is not None:
        message['Subject'] = subject

    if content is not None:
        message['HtmlBody'] = content

    if attachments:
        attachments = (
            a if isinstance(a, Attachment) else Attachment(a)
            for a in attachments
        )
        message['Attachments'] = [a.prepare() for a in attachments]

    if headers:
        message['Headers'] = [
            {'Name': k, 'Value': v} for k, v in headers.items()
        ]

    return message
