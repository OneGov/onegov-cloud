from pdftotext import PDF


def extract_pdf_info(content):
    """ Extracts the number of pages and text from a PDF.

    Requires poppler.
    """
    try:
        content.seek(0)
    except Exception:
        pass

    pages = PDF(content)
    return len(pages), '\n'.join(pages).strip(' \t\r\n').replace('\0', '')
