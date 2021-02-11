from io import BytesIO

from qrcode import QRCode, ERROR_CORRECT_H


class QrCodeMixin:

    _border = 4
    _box_size = 10
    _fill_color = 'black'
    _back_color = 'white'
    _format = 'png'

    @property
    def image(self):
        """
        Create an image from the payload
        """
        qr = QRCode(
            error_correction=ERROR_CORRECT_H,
            box_size=self._box_size,
            border=self._border
        )
        qr.add_data(self.payload)
        # Fit will determine the version depending on the size of the payload
        qr.make(fit=True)
        img = qr.make_image(
            fill_color=self._fill_color,
            back_color=self._back_color
        )
        file = BytesIO()
        img.save(file, format=self._format)
        file.seek(0)
        return file


class QrCode(QrCodeMixin):
    """ Generates QR Codes """

    def __init__(self, payload):
        self.payload = payload

    @classmethod
    def from_payload(cls, payload):
        return cls(payload).image
