from __future__ import annotations

from pdfrw import PdfReader  # type:ignore[import-untyped]
from pdfrw.buildxobj import pagexobj  # type:ignore[import-untyped]
from pdfrw.toreportlab import makerl  # type:ignore[import-untyped]
from reportlab.platypus import Flowable


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath, SupportsRead


class InlinePDF(Flowable):
    """ A flowable containing a PDF. """

    def __init__(
        self,
        pdf_file: StrOrBytesPath | SupportsRead[bytes],
        width: float
    ):
        Flowable.__init__(self)
        # FIXME: Can we re-implement this using pypdf? This is the only
        #        thing we use pdfrw for and it's not really maintained
        #        anymore...
        page = PdfReader(pdf_file, decompress=False).pages[0]
        self.page = pagexobj(page)
        self.scale = width / self.page.BBox[2]
        self.width = width
        self.height = self.page.BBox[3] * self.scale
        self.hAlign = 'CENTER'

    def wrap(self, *args: object) -> tuple[float, float]:
        return (self.width, self.height)

    def draw(self) -> None:
        rl_obj = makerl(self.canv, self.page)
        self.canv.scale(self.scale, self.scale)
        self.canv.doForm(rl_obj)
