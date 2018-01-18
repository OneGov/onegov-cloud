from copy import deepcopy
from datetime import date
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
from reportlab.platypus import ListFlowable
from reportlab.platypus import Paragraph


def test_pdf_fit_size():

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


def test_pdf():

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


def test_pdf_mini_html():
    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_a4_portrait()

    html = """<h1>Ipsum</h1>
    <p><strong>Pellentesque habitant morbi tristique</strong> senectus et
    <span style="font-size: 20">netus</span> et malesuada fames ac turpis.</p>
    <p>Donec eu libero sit amet quam egestas semper. <em>Aenean ultricies mi
    vitae est</em>. Mauris <code>commodo vitae</code>.</p>
    <p><a href="#" target="_blank">Donec non enim</a> in turpis pulvinar
    facilisis. Ut felis.</p>
    <h2>Aliquam</h2>
    <ol>
       <li>Lorem ipsum dolor sit amet, consectetuer adipiscing elit.</li>
       <li class="last">Aliquam tincidunt mauris eu risus.</li>
    </ol>
    <blockquote>
        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
    </blockquote>
    <h3>Aenean</h3>
    <ul>
       <li>Lorem ipsum dolor sit amet, consectetuer adipiscing elit.</li>
       <li>Aliquam tincidunt mauris eu risus.</li>
    </ul>
    <pre><code>
    #header h1 a {
      display: block;
      width: 300px;
      height: 80px;
    }
    </code></pre>
    """
    pdf.mini_html(html)

    paragraphs = [p.text for p in pdf.story if isinstance(p, Paragraph)]
    assert paragraphs[0] == 'Ipsum'
    assert paragraphs[1] == (
        '<strong>Pellentesque habitant morbi tristique</strong> senectus '
        'et netus et malesuada fames ac turpis.'
    )
    assert paragraphs[2] == (
        'Donec eu libero sit amet quam egestas semper. <em>Aenean '
        'ultricies mi vitae est</em>. Mauris commodo vitae.'
    )
    assert paragraphs[3] == (
        'Donec non enim in turpis pulvinar facilisis. Ut felis. Aliquam'
    )
    assert paragraphs[4] == (
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean'
    )

    lists = [
        [li.text for li in l._flowables]
        for l in pdf.story if isinstance(l, ListFlowable)
    ]
    assert lists == [
        [
            'Lorem ipsum dolor sit amet, consectetuer adipiscing elit.',
            'Aliquam tincidunt mauris eu risus.'
        ],
        [
            'Lorem ipsum dolor sit amet, consectetuer adipiscing elit.',
            'Aliquam tincidunt mauris eu risus.'
        ]
    ]

    pdf.generate()

    file.seek(0)
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 1
    assert reader.getPage(0).extractText() == (
        'Ipsum\n'
        'Pellentesque habitant morbi tristique senectus et netus et '
        'malesuada fames ac turpis.\n'
        'Donec eu libero sit amet quam egestas semper. Aenean ultricies mi '
        'vitae est. Mauris commodo vitae.\n'
        'Donec non enim in turpis pulvinar facilisis. Ut felis. Aliquam\n'
        '1\nLorem ipsum dolor sit amet, consectetuer adipiscing elit.\n'
        '2\nAliquam tincidunt mauris eu risus.\n'
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean\n'
        '\nLorem ipsum dolor sit amet, consectetuer adipiscing elit.\n'
        '\nAliquam tincidunt mauris eu risus.\n'
    )


def test_pdf_mini_html_strip():
    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_a4_portrait()
    html = (
        '<p>Eins zwei drei.</p>'
        '<p> Eins zwei drei.</p>'
        '<p>   Eins zwei drei.</p>'
        '<p>Eins zwei drei. </p>'
        '<p>Eins zwei drei.   </p>'
        '<p> Eins zwei drei. </p>'
        '<p>   Eins zwei drei.   </p>'
        '<p><em>Eins</em> zwei drei.</p>'
        '<p><em>Eins </em>zwei drei.</p>'
        '<p><em>Eins   </em>zwei drei.</p>'
        '<p>Eins <em>zwei</em> drei.</p>'
        '<p>Eins  <em>zwei</em>  drei.</p>'
        '<p>Eins<em> zwei</em> drei.</p>'
        '<p>Eins<em>  zwei</em>  drei.</p>'
        '<p>Eins <em>zwei </em>drei.</p>'
        '<p>Eins  <em>zwei  </em>drei.</p>'
        '<p>Eins<em> zwei </em>drei.</p>'
        '<p>Eins<em>  zwei  </em>drei.</p>'
        '<p>Eins zwei <em>drei</em>.</p>'
        '<p>Eins zwei  <em>drei</em>.</p>'
        '<p>Eins zwei<em> drei</em>.</p>'
        '<p>Eins zwei<em>  drei</em>.</p>'
    )
    pdf.mini_html(html)
    paras = [p.text for p in pdf.story if isinstance(p, Paragraph)]
    assert paras == [
        'Eins zwei drei.',
        'Eins zwei drei.',
        'Eins zwei drei.',
        'Eins zwei drei.',
        'Eins zwei drei.',
        'Eins zwei drei.',
        'Eins zwei drei.',
        '<em>Eins</em> zwei drei.',
        '<em>Eins </em>zwei drei.',
        '<em>Eins </em>zwei drei.',
        'Eins <em>zwei</em> drei.',
        'Eins <em>zwei</em> drei.',
        'Eins<em> zwei</em> drei.',
        'Eins<em> zwei</em> drei.',
        'Eins <em>zwei </em>drei.',
        'Eins <em>zwei </em>drei.',
        'Eins<em> zwei </em>drei.',
        'Eins<em> zwei </em>drei.',
        'Eins zwei <em>drei</em>.',
        'Eins zwei <em>drei</em>.',
        'Eins zwei<em> drei</em>.',
        'Eins zwei<em> drei</em>.',
    ]
    paras = [p.replace('<em>', '').replace('</em>', '') for p in paras]
    assert set(paras) == {'Eins zwei drei.'}

    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_a4_portrait()
    html = (
        '<p>Eins <em>zwei</em> drei <em>vier</em> .</p>'
        '<p>Eins   <em>zwei</em>   drei   <em>vier</em>   .</p>'
        '<p> Eins<em> zwei</em> drei<em> vier</em> .</p>'
        '<p>  Eins<em>  zwei</em>  drei<em>  vier</em>  .</p>'
        '<p>Eins <em>zwei </em>drei <em>vier </em>.</p>'
        '<p>Eins  <em>zwei  </em>drei  <em>vier  </em>.</p>'
        '<p>Eins<em> zwei </em>drei<em> vier </em>.</p>'
        '<p>Eins<em>   zwei   </em>drei<em>   vier   </em>.</p>'
        '<p>Eins <em>zwei</em> drei<em> vier </em>.</p>'
        '<p>Eins   <em>zwei</em>   drei<em>   vier   </em>.</p>'
        '<p>Eins<em> zwei</em> drei <em>vier </em>.</p>'
        '<p>Eins<em>   zwei</em>   drei   <em>vier   </em>.</p>'
    )
    pdf.mini_html(html)
    paras = [p.text for p in pdf.story if isinstance(p, Paragraph)]
    assert paras == [
        'Eins <em>zwei</em> drei <em>vier</em> .',
        'Eins <em>zwei</em> drei <em>vier</em> .',
        'Eins<em> zwei</em> drei<em> vier</em> .',
        'Eins<em> zwei</em> drei<em> vier</em> .',
        'Eins <em>zwei </em>drei <em>vier </em>.',
        'Eins <em>zwei </em>drei <em>vier </em>.',
        'Eins<em> zwei </em>drei<em> vier </em>.',
        'Eins<em> zwei </em>drei<em> vier </em>.',
        'Eins <em>zwei</em> drei<em> vier </em>.',
        'Eins <em>zwei</em> drei<em> vier </em>.',
        'Eins<em> zwei</em> drei <em>vier </em>.',
        'Eins<em> zwei</em> drei <em>vier </em>.',

    ]
    paras = [p.replace('<em>', '').replace('</em>', '') for p in paras]
    assert set(paras) == {'Eins zwei drei vier .'}


def test_page_fn_header():
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


def test_page_fn_footer():
    year = date.today().year

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
    assert reader.getPage(0).extractText() == f'© {year} author\n1\n'


def test_page_fn_header_and_footer():
    year = date.today().year

    file = BytesIO()
    pdf = Pdf(file, title='title', author='author')
    pdf.init_a4_portrait(page_fn_header_and_footer)
    pdf.pagebreak()
    pdf.pagebreak()
    pdf.generate()

    file.seek(0)
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 2
    assert reader.getPage(0).extractText() == f'title\n© {year} author\n1\n'
    assert reader.getPage(1).extractText() == f'title\n© {year} author\n2\n'
