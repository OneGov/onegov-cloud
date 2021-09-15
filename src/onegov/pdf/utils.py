from pdftotext import PDF


def extract_pdf_info(content):
    """ Extracts the number of pages and text from a PDF.

    Requires poppler.
    """
    if hasattr(content, 'seek'):
        content.seek(0)
    pages = PDF(content)
    return len(pages), '\n'.join(pages).strip(' \t\r\n').replace('\0', '')
