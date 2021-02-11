
from onegov.qrcode import QrCode


def test_qr_code_image():

    img = QrCode.from_payload('https://seantis.ch')
    path = '/tmp/qrcode.png'
    with open(path, 'wb') as f:
        f.write(img.getvalue())
