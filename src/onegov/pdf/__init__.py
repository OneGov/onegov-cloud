from __future__ import annotations

import logging

from onegov.pdf.page_functions import page_fn_footer
from onegov.pdf.page_functions import page_fn_header
from onegov.pdf.page_functions import page_fn_header_and_footer
from onegov.pdf.page_functions import page_fn_header_logo
from onegov.pdf.page_functions import page_fn_header_logo_and_footer
from onegov.pdf.pdf import Pdf

log = logging.getLogger('onegov.pdf')
log.addHandler(logging.NullHandler())


__all__ = (
    'log',
    'page_fn_footer',
    'page_fn_header_and_footer',
    'page_fn_header_logo_and_footer',
    'page_fn_header_logo',
    'page_fn_header',
    'Pdf',
)
