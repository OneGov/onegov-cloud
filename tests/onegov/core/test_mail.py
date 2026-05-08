from __future__ import annotations

from email.headerregistry import Address
from email.policy import SMTP

from onegov.core.mail import format_single_address
from onegov.core.mail import needs_qp_encode


def addr(email: str, name: str = '') -> Address:
    # let's keep the code a bit shorter...
    return Address(name, addr_spec=email)


def test_needs_qp_encode() -> None:
    assert needs_qp_encode('test') is False
    assert needs_qp_encode('"') is True
    assert needs_qp_encode('ö') is True


def test_format_single_address() -> None:
    # basic case
    assert format_single_address(
        addr('test@example.com')
    ) == 'test@example.com'
    # basic case with a display name
    assert format_single_address(
        addr('test@example.com', 'Test')
    ) == 'Test <test@example.com>'
    # display name with special character
    assert format_single_address(
        addr('test@example.com', 'Test.')
    ) == '"Test." <test@example.com>'
    # display name with double quote
    assert format_single_address(
        addr('test@example.com', 'Test"')
    ) == '=?utf-8?q?Test=22?= <test@example.com>'
    # display name with non-ascii character
    assert format_single_address(
        addr('test@example.com', 'Test ä')
    ) == '=?utf-8?q?Test_=C3=A4?= <test@example.com>'
    # too long qp encoded display name
    name = 'Test "' + 'a' * 160
    formatted = format_single_address(
        addr('test@example.com', name)
    )
    assert formatted == (
        '"=?utf-8?q?Test_=22' + 'a' * 55
        + '?= =?utf-8?q?' + 'a' * 63
        + '?= =?utf-8?q?' + 'a' * 42
        + '?=" <test@example.com>'
    )
    # make sure we can still parse this as a header
    header = SMTP.header_factory('sender', formatted)
    # and we end up back with what we put in originally
    assert header.address.display_name == name

    # extract only the encoded words from the formatted address
    words = formatted[1:-len('" <test@example.com>')].split(' ')
    # make sure each word is at most 75 characters
    assert all(len(part) <= 75 for part in words)


def test_format_single_address_coerced() -> None:
    # basic case
    assert format_single_address('test@example.com') == 'test@example.com'
    # basic case with a display name
    assert format_single_address(
        'Test <test@example.com>'
    ) == 'Test <test@example.com>'
    # display name with special character
    assert format_single_address(
        '"Test." <test@example.com>'
    ) == '"Test." <test@example.com>'
    # display name with double quote
    assert format_single_address(
        '=?utf-8?q?Test=22?= <test@example.com>'
    ) == '=?utf-8?q?Test=22?= <test@example.com>'
    # display name with non-ascii character
    assert format_single_address(
        '=?utf-8?q?Test_=C3=A4?= <test@example.com>'
    ) == '=?utf-8?q?Test_=C3=A4?= <test@example.com>'
    # too long qp encoded display name, either split up into
    # multiple words or with a single big one that would be
    # rejected by Postmark
    too_long_unsplit = (
        '=?utf-8?q?Test_=22' + 'a' * 160 + '?=  <test@example.com>'
    )
    too_long_split = (
        '"=?utf-8?q?Test_=22' + 'a' * 55
        + '?= =?utf-8?q?' + 'a' * 63
        + '?= =?utf-8?q?' + 'a' * 42
        + '?=" <test@example.com>'
    )
    assert format_single_address(
        too_long_split
    ) == too_long_split
    assert format_single_address(
        too_long_unsplit
    ) == too_long_split
