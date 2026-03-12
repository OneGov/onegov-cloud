from __future__ import annotations

import magic
from onegov.qrcode import QrCode


def test_qr_code_image() -> None:
    img = QrCode.from_payload('https://seantis.ch')
    # did we generate a png file?
    assert magic.from_buffer(img.getvalue(), mime=True) == 'image/png'
