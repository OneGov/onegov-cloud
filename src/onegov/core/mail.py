import os.path
import magic
import re

from base64 import b64encode
from email.headerregistry import Address
from email.policy import SMTP
from onegov.core.html import html_to_text
from string import ascii_letters, digits


specials_regex = re.compile(r'[][\\()<>@,:;.]')
alphanumeric = ascii_letters + digits
qp_prefix = '=?utf-8?q?'
qp_suffix = '?='
QP_PREFIX_LENGTH = len(qp_prefix)
QP_SUFFIX_LENGTH = len(qp_suffix)
QP_MAX_WORD_LENGTH = 75
QP_CONTENT_LENGTH = QP_MAX_WORD_LENGTH - QP_PREFIX_LENGTH - QP_SUFFIX_LENGTH


def needs_qp_encode(display_name):
    # NOTE: Backslash escaping is forbidden in Postmark API
    if '"' in display_name:
        return True
    try:
        # NOTE: Technically there's some ASCII characters that
        #       should be illegal altogether such as \n, \r, \0
        #       This should already be caught by the use of Address
        #       though, which makes sure each part only contains
        #       legal characters.
        display_name.encode('ascii')
    except UnicodeEncodeError:
        return True
    return False


def qp_encode_display_name(display_name):
    """
    Applies Quoted Printable encoding to the display name according
    to Postmark API's rules that can be parsed losslessly back into
    the original display_name with the EmailMessage API.
    """
    words = []
    current_word = []

    def finish_word() -> None:
        nonlocal current_word
        content = ''.join(current_word)
        words.append(f'{qp_prefix}{content}{qp_suffix}')
        current_word = []

    for character in display_name:
        if character == ' ':
            # special case for header encoding
            characters = ['_']
        elif character in alphanumeric:
            # no need to encode this character
            characters = [character]
        else:
            # QP encode the character
            characters = list(
                ''.join(f'={c:02X}' for c in character.encode('utf-8'))
            )

        if len(current_word) + len(characters) > QP_CONTENT_LENGTH:
            finish_word()

        current_word.extend(characters)

    finish_word()
    if len(words) == 1:
        # We can omit the enclosing double quotes
        return words[0]

    # NOTE: The enclosing double quotes are necessary so that spaces
    #       as word separators can be parsed correctly.
    return f'"{" ".join(words)}"'


def coerce_address(address):
    """
    Coerces a string type into a email.headerregistry.Address object
    by parsing the string as a sender header.

    It acts like parseaddr for string values, but undoes QP-encoding
    for the display_name which parseaddr does not.

    NOTE: This function should probably go away, once we switch to
          using Address objects everywhere. Or we make it more strict
          by asserting that string values need to be an email address
          without display_name, so we can use Address(addr_spec=address)
          to coerce it, which should be faster than header_factory.
    """
    if isinstance(address, str):
        header = SMTP.header_factory('sender', address)
        return header.address

    assert isinstance(address, Address)
    return address


def format_single_address(address):
    """
    Formats a single Address according to Postmark API rules that is
    cross-compatible with email.message.EmailMessage for raw SMTP sends.

    The rules state that backslash escaping quotes is illegal and quoted
    printable encoded display names need to be split into space-separated
    encoded words of maximum length 75, with the entire display name
    enclosed in double quotes if it contains more than one word.

    :param address: email.headerregistry.Address or preformatted string
    """
    address = coerce_address(address)
    name = address.display_name
    if not name:
        return address.addr_spec

    if not needs_qp_encode(name):
        if specials_regex.search(name):
            # simple quoting works here, since we disallow
            # backslash escaping double quotes.
            name = f'"{name}"'
        return f'{name} <{address.addr_spec}>'

    name = qp_encode_display_name(name)
    return f'{name} <{address.addr_spec}>'


def format_address(addresses):
    """
    Convenience function that accepts both a single Address and a
    sequence of Address, otherwise identical to format_single_address

    It enforces a limit of 50 addresses, due to Postmark API restrictions

    :param addresses: Single Address/str or sequence thereof
    """
    if isinstance(addresses, (Address, str)):
        return format_single_address(addresses)

    assert len(addresses) <= 50
    return ', '.join(format_single_address(a) for a in addresses)


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

    if not plaintext:
        # if no plaintext is given we require content
        assert content

        # turn the html email into a plaintext representation
        # this leads to a lower spam rating
        plaintext = html_to_text(content)

    message = {
        'From': format_single_address(sender),
        'To': format_address(receivers),
        'TextBody': plaintext,
        'MessageStream': stream,
    }

    if reply_to is not None:
        # we require address objects so we can modify them
        sender = coerce_address(sender)
        reply_to = coerce_address(reply_to)
        message['ReplyTo'] = format_single_address(reply_to)

        # if the reply to address has a name part (Name <address@host>), use
        # the display_name for the sender address as well to somewhat hide the
        # fact that we're using a noreply email
        if reply_to.display_name and not sender.display_name:
            sender = Address(
                reply_to.display_name,
                sender.username,
                sender.domain
            )
            message['From'] = format_single_address(sender)

    if cc:
        message['Cc'] = format_address(cc)

    if bcc:
        message['Bcc'] = format_address(bcc)

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
