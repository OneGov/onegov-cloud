from onegov.file.security.pdfid import PDFiD
from tempfile import NamedTemporaryFile
from shutil import copyfileobj


def sanitize_pdf(input):
    """ Takes a fileobject pointing to a PDF and sanitizes it by removing
    potentially dangerous content.

    The return value is a path that points to the disarmed file.

    """

    # we need to write the file to a temporary location
    with NamedTemporaryFile() as output:
        copyfileobj(input, output)
        output.flush()

        PDFiD(output.name, disarm=True)
        return f'{output.name}.disarmed'
