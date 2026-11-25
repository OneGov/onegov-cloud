from __future__ import annotations

import base64

from onegov.qrcode import QrCode


def test_encoded_image() -> None:
    raw = QrCode('https://example.org').encoded_image
    assert isinstance(raw, bytes)
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'  # png signature

    encoded = QrCode('https://example.org', encoding='base64').encoded_image
    assert isinstance(encoded, bytes)
    # the base64 output decodes back to a png
    assert base64.b64decode(encoded)[:8] == b'\x89PNG\r\n\x1a\n'


def test_content_type() -> None:
    assert QrCode('x').content_type == 'image/png'
    assert QrCode('x', encoding='base64').content_type == 'image/png;base64'
