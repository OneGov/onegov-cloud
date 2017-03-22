from copy import deepcopy
from io import BytesIO
from onegov.election_day.utils.pdf import Pdf
from pdfdocument.document import MarkupParagraph
from pdfrw import PdfReader
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph


def test_pdf_document_fit_size():

    def floor(*args):
        return tuple(int(arg) for arg in args)

    pdf = Pdf(BytesIO())
    pdf.init_a4_portrait()

    m_w = pdf.doc.width
    m_h = pdf.doc.height * 0.9

    assert floor(*pdf.fit_size(1 * cm, 1 * cm)) == floor(m_w, m_w)
    assert floor(*pdf.fit_size(2 * cm, 1 * cm)) == floor(m_w, m_w / 2)
    assert floor(*pdf.fit_size(1 * cm, 2 * cm)) == floor(m_h / 2, m_h)

    assert floor(*pdf.fit_size(100 * cm, 100 * cm)) == floor(m_w, m_w)
    assert floor(*pdf.fit_size(200 * cm, 100 * cm)) == floor(m_w, m_w / 2)
    assert floor(*pdf.fit_size(100 * cm, 200 * cm)) == floor(m_h / 2, m_h)

    m_w = 0.9 * pdf.doc.width
    m_h = 0.9 * pdf.doc.height * 0.9

    assert floor(*pdf.fit_size(1 * cm, 1 * cm, 0.9)) == floor(m_w, m_w)
    assert floor(*pdf.fit_size(2 * cm, 1 * cm, 0.9)) == floor(m_w, m_w / 2)
    assert floor(*pdf.fit_size(1 * cm, 2 * cm, 0.9)) == floor(m_h / 2, m_h)

    assert floor(*pdf.fit_size(100 * cm, 100 * cm, 0.9)) == floor(m_w, m_w)
    assert floor(*pdf.fit_size(200 * cm, 100 * cm, 0.9)) == floor(m_w, m_w / 2)
    assert floor(*pdf.fit_size(100 * cm, 200 * cm, 0.9)) == floor(m_h / 2, m_h)


def test_pdf_document():

    f = BytesIO()
    pdf = Pdf(f)
    pdf.init_a4_portrait()

    pdf.h1('Test Document')
    pdf.pagebreak()

    fi = BytesIO()
    inline = Pdf(fi)
    inline.init_report()
    inline.p('This is paragraph')
    inline.generate()
    fi.seek(0)
    pdf.pdf(fi)
    pdf.figcaption('a figure')
    pdf.pagebreak()

    pdf.table([[1, 2, 3]], 'even')
    assert len(set(pdf.story[-1]._colWidths)) == 1
    assert int(sum(pdf.story[-1]._colWidths)) == int(pdf.doc.width)
    pdf.pagebreak()

    pdf.table([[1, 2, 3, 4, 5]], [2, 1, 1, 1, 2], ratios=True)
    assert len(set(pdf.story[-1]._colWidths)) == 2
    assert int(sum(pdf.story[-1]._colWidths)) == int(pdf.doc.width)
    pdf.pagebreak()

    pdf.table([[1, 2, 3]], [1 * cm, 1 * cm, 1 * cm])
    assert len(set(pdf.story[-1]._colWidths)) == 1
    pdf.pagebreak()

    style = deepcopy(pdf.style.normal)
    style.fontSize = 20
    pdf.table([['1', '2', MarkupParagraph('3', style)]], None)
    row = pdf.story[-1]._cellvalues[0]
    assert all([isinstance(cell, Paragraph) for cell in row])
    assert [p.style.fontSize for p in row] == [10, 10, 20]
    pdf.pagebreak()

    style = pdf.style.table + (
        ('ALIGN', (0, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (2, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
    )
    pdf.table([['right', 'left', 'center']], None, style=style)
    row = pdf.story[-1]._cellvalues[0]
    assert [p.style.alignment for p in row] == [TA_RIGHT, TA_LEFT, TA_CENTER]

    pdf.generate()
    f.seek(0)
    assert len(PdfReader(f, decompress=False).pages) == 7
