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
            box_size=self.box_size,
            border=self.border
        )
        qr.add_data(self.payload)
        # Fit will determine the version depending on the size of the payload
        qr.make(fit=True)
        img = qr.make_image(
            fill_color=self.fill_color,
            back_color=self.back_color
        )
        file = BytesIO()
        img.save(file, format=self.img_format)
        file.seek(0)
        return file


class QrCode(QrCodeMixin):
    """ Generates QR Codes """

    def __init__(self, payload, border=None, box_size=None, fill_color=None,
                 back_color=None, img_format=None):
        self.payload = payload
        self.border = border or self._border
        self.box_size = box_size or self._box_size
        self.fill_color = fill_color or self._fill_color
        self.back_color = back_color or self._back_color
        self.img_format = img_format or self._format

    @classmethod
    def from_payload(cls, payload):
        return cls(payload).image
