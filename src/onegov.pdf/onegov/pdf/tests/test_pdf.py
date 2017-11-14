from copy import deepcopy
from io import BytesIO
from onegov.pdf import page_fn_footer
from onegov.pdf import page_fn_header
from onegov.pdf import page_fn_header_and_footer
from onegov.pdf import Pdf
from pdfdocument.document import MarkupParagraph
from pdfrw import PdfReader
from PyPDF2 import PdfFileReader
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.enums import TA_RIGHT
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


def test_header():
    # no title
    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_a4_portrait(page_fn_header)
    pdf.generate()

    file.seek(0)
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 1
    assert reader.getPage(0).extractText() == ''

    # title
    file = BytesIO()
    pdf = Pdf(file, title='title')
    pdf.init_a4_portrait(page_fn_header)
    pdf.generate()

    file.seek(0)
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 1
    assert reader.getPage(0).extractText() == 'title\n'

    # long title
    title = (
        'This is a very long title so that it breaks the header line to '
        'a second line which must also be ellipsed.'
        'It is really, really, really, really, really, really, really, '
        'really, really, really, really, really, really, really, really, '
        'really, really, really, really, really, really, really, really, '
        'really, really, really, really, really, really, really, really, '
        'really a long title!'
    )

    file = BytesIO()
    pdf = Pdf(file, title=title)
    pdf.init_a4_portrait(page_fn_header)
    pdf.generate()

    file.seek(0)
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 1
    assert reader.getPage(0).extractText() == (
        'This is a very long title so that it breaks the header line to a '
        'second line which must also be ellipsed.It is\n'
        'really, really, really, really, really, really, really, really, '
        'really, really, really, [...]\n'
    )


def test_footer():
    # no author
    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_a4_portrait(page_fn_footer)
    pdf.generate()

    file.seek(0)
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 1
    assert reader.getPage(0).extractText() == '1\n'

    # two pages
    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_a4_portrait(page_fn_footer)
    pdf.pagebreak()
    pdf.pagebreak()
    pdf.generate()

    file.seek(0)
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 2
    assert reader.getPage(0).extractText() == '1\n'
    assert reader.getPage(1).extractText() == '2\n'

    # author
    file = BytesIO()
    pdf = Pdf(file, author='author')
    pdf.init_a4_portrait(page_fn_footer)
    pdf.generate()

    file.seek(0)
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 1
    assert reader.getPage(0).extractText() == '© 2017 author\n1\n'


def test_header_and_footer():
    file = BytesIO()
    pdf = Pdf(file, title='title', author='author')
    pdf.init_a4_portrait(page_fn_header_and_footer)
    pdf.pagebreak()
    pdf.pagebreak()
    pdf.generate()

    file.seek(0)
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 2
    assert reader.getPage(0).extractText() == 'title\n© 2017 author\n1\n'
    assert reader.getPage(1).extractText() == 'title\n© 2017 author\n2\n'
