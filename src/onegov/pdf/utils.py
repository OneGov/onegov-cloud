from __future__ import annotations

from pdftotext import PDF  # type:ignore
from onegov.pdf import log


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRead


def extract_pdf_info(
    content: SupportsRead[bytes],
    remove: str = '\0'
) -> tuple[int, str]:
    """ Extracts the number of pages and text from a PDF.

    Requires poppler.
    """
    try:
        content.seek(0)  # type:ignore[attr-defined]
    except Exception:
        log.debug('Content does not support seek')

    pages = PDF(content)

    def clean(text: str) -> str:
        for character in remove:
            text = text.replace(character, '')
        return ' '.join(text.split())

    return (len(pages), ' '.join(clean(page) for page in pages).strip())
