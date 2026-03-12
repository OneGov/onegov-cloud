from __future__ import annotations


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_qr_code_view(client: Client) -> None:
    assert client.get('/qrcode?payload=hello').content_type == 'image/png'
    assert client.get('/qrcode?img_format=jpeg').content_type == 'image/jpeg'
    assert client.get('/qrcode?img_format=gif').content_type == 'image/gif'
    assert client.get('/qrcode?encoding=base64').content_type == 'image/png'
