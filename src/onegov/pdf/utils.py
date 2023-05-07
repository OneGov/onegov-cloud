from pdftotext import PDF
from onegov.pdf import log


def extract_pdf_info(content, remove='\0'):
    """ Extracts the number of pages and text from a PDF.

    Requires poppler.
    """
    try:
        content.seek(0)
    except Exception:
        log.warning('Invalid PDF for extraction')

    pages = PDF(content)

    def clean(text):
        for character in remove:
            text = text.replace(character, '')
        return ' '.join(text.split())

    return (len(pages), ' '.join(clean(page) for page in pages).strip())
