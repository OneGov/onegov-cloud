from base64 import b64encode
from io import BytesIO
from qrcode import QRCode, ERROR_CORRECT_H


from typing import Literal

# FIXME: This module seems honestly completely unecessary, this could
#        easily be moved to a couple of small util functions in core


class QrCode:
    """ Generates QR Codes """

    _border = 4
    _box_size = 10
    _fill_color = 'black'
    _back_color = 'white'
    _format = 'png'
    _encoding = None

    def __init__(
        self,
        payload: str | bytes,
        border: int | None = None,
        box_size: int | None = None,
        fill_color: str | None = None,
        back_color: str | None = None,
        img_format: str | None = None,
        encoding: Literal['base64'] | None = None
    ):
        self.payload = payload
        self.border = border or self._border
        self.box_size = box_size or self._box_size
        self.fill_color = fill_color or self._fill_color
        self.back_color = back_color or self._back_color
        self.img_format = img_format or self._format
        self.encoding = encoding or self._encoding

    @classmethod
    def from_payload(cls, payload: str | bytes) -> BytesIO:
        return cls(payload).image

    @property
    def image(self) -> BytesIO:
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

    @property
    def encoded_image(self) -> str | bytes:
        # FIXME: If we access both image and encoded_image this is horribly
        #        ineffcient, all so we can potentially save one line of code...
        if self.encoding == 'base64':
            return b64encode(self.image.read())
        return self.image.read()

    @property
    def content_type(self) -> str:
        encoding = self.encoding and f';{self.encoding}' or ''
        return f'image/{self.img_format}{encoding}'
