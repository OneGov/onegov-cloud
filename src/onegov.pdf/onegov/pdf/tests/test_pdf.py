from copy import deepcopy
from datetime import date
from io import BytesIO
from onegov.core.utils import module_path
from onegov.pdf import page_fn_footer
from onegov.pdf import page_fn_header
from onegov.pdf import page_fn_header_and_footer
from onegov.pdf import page_fn_header_logo
from onegov.pdf import page_fn_header_logo_and_footer
from onegov.pdf import Pdf
from pdfdocument.document import MarkupParagraph
from pdfrw import PdfReader
from PyPDF2 import PdfFileReader
from pytest import mark
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


def test_pdf_headers():

    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_a4_portrait()

    pdf.h1('h1')
    pdf.h('h1', 1)
    assert pdf.story[-1].style == pdf.story[-2].style

    pdf.h2('h2')
    pdf.h('h2', 2)
    assert pdf.story[-1].style == pdf.story[-2].style

    pdf.h3('h3')
    pdf.h('h3', 3)
    assert pdf.story[-1].style == pdf.story[-2].style

    pdf.h4('h4')
    pdf.h('h4', 4)
    assert pdf.story[-1].style == pdf.story[-2].style

    pdf.h5('h5')
    pdf.h('h5', 5)
    assert pdf.story[-1].style == pdf.story[-2].style

    pdf.h6('h6')
    pdf.h('h6', 6)
    assert pdf.story[-1].style == pdf.story[-2].style

    pdf.h('h7', 7)
    assert pdf.story[-1].style == pdf.story[-2].style

    pdf.generate()
    file.seek(0)
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 1
    assert reader.getPage(0).extractText() == (
        'h1\nh1\nh2\nh2\nh3\nh3\nh4\nh4\nh5\nh5\nh6\nh6\nh7\n'
    )


def test_pdf_toc():

    file = BytesIO()
    pdf = Pdf(file, toc_levels=6)
    pdf.init_a4_portrait()
    pdf.table_of_contents()
    pdf.pagebreak()
    pdf.h1('a')
    pdf.h2('a.a')
    pdf.pagebreak()
    pdf.h2('a.b')
    pdf.h3('a.b.a')
    pdf.h3('a.b.b')
    pdf.h4('a.b.b.a')
    pdf.h4('a.b.b.b')
    pdf.h4('a.b.b.c')
    pdf.h3('a.b.c')
    pdf.pagebreak()
    pdf.h2('a.c')
    pdf.h3('a.c.a')
    pdf.h4('a.c.a.a')
    pdf.h5('a.c.a.a.a')
    pdf.h5('a.c.a.a.b')
    pdf.h6('a.c.a.a.b.a')
    pdf.h6('a.c.a.a.b.b')

    pdf.generate()
    file.seek(0)

    reader = PdfFileReader(file)
    assert reader.getNumPages() == 4
    assert reader.getPage(0).extractText() == (
        '2\n1 a\n'
        '2\n1.1 a.a\n'
        '3\n1.2 a.b\n'
        '3\n1.2.1 a.b.a\n'
        '3\n1.2.2 a.b.b\n'
        '3\n1.2.2.1 a.b.b.a\n'
        '3\n1.2.2.2 a.b.b.b\n'
        '3\n1.2.2.3 a.b.b.c\n'
        '3\n1.2.3 a.b.c\n'
        '4\n1.3 a.c\n'
        '4\n1.3.1 a.c.a\n'
        '4\n1.3.1.1 a.c.a.a\n'
        '4\n1.3.1.1.1 a.c.a.a.a\n'
        '4\n1.3.1.1.2 a.c.a.a.b\n'
        '4\n1.3.1.1.2.1 a.c.a.a.b.a\n'
        '4\n1.3.1.1.2.2 a.c.a.a.b.b\n'
    )
    assert reader.getPage(1).extractText() == '1 a\n1.1 a.a\n'
    assert reader.getPage(2).extractText() == (
        '1.2 a.b\n'
        '1.2.1 a.b.a\n'
        '1.2.2 a.b.b\n'
        '1.2.2.1 a.b.b.a\n'
        '1.2.2.2 a.b.b.b\n'
        '1.2.2.3 a.b.b.c\n'
        '1.2.3 a.b.c\n'
    )
    assert reader.getPage(3).extractText() == (
        '1.3 a.c\n'
        '1.3.1 a.c.a\n'
        '1.3.1.1 a.c.a.a\n'
        '1.3.1.1.1 a.c.a.a.a\n'
        '1.3.1.1.2 a.c.a.a.b\n'
        '1.3.1.1.2.1 a.c.a.a.b.a\n'
        '1.3.1.1.2.2 a.c.a.a.b.b\n'
    )


def test_pdf_toc_levels():

    file = BytesIO()
    pdf = Pdf(file, toc_levels=2)
    pdf.init_a4_portrait()
    pdf.table_of_contents()
    pdf.h1('a')
    pdf.h2('a.a')
    pdf.h3('a.a.a')
    pdf.h4('a.a.a.a')
    pdf.h5('a.a.a.a.a')
    pdf.h6('a.a.a.a.a.a')

    pdf.generate()
    file.seek(0)

    reader = PdfFileReader(file)
    assert reader.getNumPages() == 1
    assert reader.getPage(0).extractText() == (
        '1\n1 a\n'
        '1\n1.1 a.a\n'
        '1 a\n'
        '1.1 a.a\n'
        '1.1.1 a.a.a\n'
        '1.1.1.1 a.a.a.a\n'
        '1.1.1.1.1 a.a.a.a.a\n'
        '1.1.1.1.1.1 a.a.a.a.a.a\n'
    )


@mark.parametrize("path", [
    module_path('onegov.pdf', 'tests/fixtures/onegov.jpg'),
    module_path('onegov.pdf', 'tests/fixtures/onegov.png'),
])
def test_pdf_image(path):
    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_a4_portrait()
    pdf.image(path)
    pdf.generate()
    file.seek(0)

    assert len(PdfReader(file, decompress=False).pages) == 1

    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_a4_portrait()
    with open(path, 'rb') as f:
        pdf.image(BytesIO(f.read()), factor=0.5)
    pdf.generate()
    file.seek(0)

    assert len(PdfReader(file, decompress=False).pages) == 1


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


def test_pdf_mini_html_linkify():
    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_a4_portrait()

    html = """
    <p>
        <a href="#" target="blank" class="external">Pellentesque habitant</a>
         morbi senectus et http://netuset.et turpis mal@fames.ac.
    </p>
    """
    pdf.mini_html(html, linkify=True)
    paras = [p.text for p in pdf.story if isinstance(p, Paragraph)]
    assert paras == [
        '<a color="#00538c" href="#">Pellentesque habitant</a>'
        ' morbi senectus et '
        '<a color="#00538c" href="http://netuset.et">http://netuset.et</a>'
        ' turpis '
        '<a color="#00538c" href="mailto:mal@fames.ac">mal@fames.ac</a>'
        '.'
    ]


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

    # created
    file = BytesIO()
    pdf = Pdf(file, created='created')
    pdf.init_a4_portrait(page_fn_header)
    pdf.generate()

    file.seek(0)
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 1
    assert reader.getPage(0).extractText() == 'created\n'


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


@mark.parametrize("path", [
    module_path('onegov.pdf', 'tests/fixtures/onegov.svg'),
])
def test_page_fn_header_logo(path):
    with open(path) as file:
        logo = file.read()

    # no logo
    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_a4_portrait(page_fn_header_logo)
    pdf.generate()

    file.seek(0)
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 1
    assert reader.getPage(0).extractText() == ''

    # logo
    file = BytesIO()
    pdf = Pdf(file, logo=logo)
    pdf.init_a4_portrait(page_fn_header_logo)
    pdf.generate()

    file.seek(0)
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 1
    assert reader.getPage(0).extractText() == 'onegov.ch\n'


@mark.parametrize("path", [
    module_path('onegov.pdf', 'tests/fixtures/onegov.svg'),
])
def test_page_fn_header_logo_and_footer(path):
    with open(path) as file:
        logo = file.read()

    file = BytesIO()
    pdf = Pdf(file, author='author', logo=logo)
    pdf.init_a4_portrait(page_fn_header_logo_and_footer)
    pdf.generate()

    file.seek(0)
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 1
    assert reader.getPage(0).extractText() == 'onegov.ch\n© 2018 author\n1\n'
