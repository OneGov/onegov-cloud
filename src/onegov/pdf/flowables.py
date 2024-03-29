from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl
from reportlab.platypus import Flowable


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath, SupportsRead


class InlinePDF(Flowable):
    """ A flowable containing a PDF. """

    def __init__(
        self,
        pdf_file: 'StrOrBytesPath | SupportsRead[bytes]',
        width: float
    ):
        Flowable.__init__(self)
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
