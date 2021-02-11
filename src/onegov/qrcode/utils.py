from pyzbar.pyzbar import decode
from PIL import Image


def decode_qr(stream):
    """
    Encodes
    """
    img = Image.open(stream)
    decoded = decode(img)
    return "\n".join(i.data.decode('utf-8') for i in decoded)
