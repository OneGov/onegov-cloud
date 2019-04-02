from datetime import date, datetime
from onegov.org import utils


def test_annotate_html():
    html = "<p><img/></p><p></p>"
    assert utils.annotate_html(html) == (
        '<p class="has-img"><img class="lazyload-alt"></p><p></p>'
    )

    html = "<p class='x'><img/></p><p></p>"
    assert utils.annotate_html(html) == (
        '<p class="x has-img"><img class="lazyload-alt"></p><p></p>'
    )

    html = "<strong></strong>"
    assert utils.annotate_html(html) == html

    html = '<a href="http://www.seantis.ch"></a>'
    assert utils.annotate_html(html) == html

    html = 'no html'
    assert utils.annotate_html(html) == 'no html'

    html = '<p><a href="http://www.seantis.ch"></a></p>'
    assert utils.annotate_html(html) == html

    html = (
        '<p><a href="https://www.youtube.com/watch?v=dQw4w9WgXcQ"></a></p>'
    )
    assert '<p class="has-video">' in utils.annotate_html(html)
    assert 'class="has-video"></a>' in utils.annotate_html(html)

    html = (
        '<p>'
        '<a href="https://www.youtube.com/watch?v=dQw4w9WgXcQ"></a>'
        '<img />'
        '</p>'
    )
    assert '<p class="has-img has-video">' in utils.annotate_html(html)
    assert 'class="has-video"></a>' in utils.annotate_html(html)

    html = (
        '<p># foo, #bar, #baz qux</p>'
    )

    assert "has-hashtag" in utils.annotate_html('<p>#foo</p>')
    assert "has-hashtag" in utils.annotate_html('<p>#bar</p>')
    assert "has-hashtag" not in utils.annotate_html('<p>#xy</p>')


def test_remove_empty_paragraphs():
    html = "<p><br></p>"
    assert utils.remove_empty_paragraphs(html) == ""

    # multiple br elements added by shift+enter are left alone (this is
    # a way to manually override the empty paragraphs removal)
    html = "<p><br><br></p>"
    assert utils.remove_empty_paragraphs(html) == "<p><br><br></p>"

    html = "<p> <br></p>"
    assert utils.remove_empty_paragraphs(html) == ""

    html = "<p>hey</p>"
    assert utils.remove_empty_paragraphs(html) == "<p>hey</p>"

    html = "<p><img></p>"
    assert utils.remove_empty_paragraphs(html) == "<p><img></p>"


def test_predict_next_value():
    assert utils.predict_next_value((1, )) is None
    assert utils.predict_next_value((1, 1)) is None
    assert utils.predict_next_value((1, 1, 1)) == 1
    assert utils.predict_next_value((2, 1, 2, 1)) == 2
    assert utils.predict_next_value((1, 2, 1, 2)) == 1
    assert utils.predict_next_value((2, 2, 2, 1)) is None
    assert utils.predict_next_value((2, 4, 6)) == 8
    assert utils.predict_next_value((1, 2, 3)) == 4
    assert utils.predict_next_value((1, 2, 3, 5)) is None
    assert utils.predict_next_value((1, 2, 3, 5, 6), min_probability=0) == 7
    assert utils.predict_next_value((1, 2, 3, 5, 6), min_probability=.5) == 7
    assert utils.predict_next_value(
        (1, 2, 3, 5, 6), min_probability=.6) is None


def test_predict_next_daterange():
    assert utils.predict_next_daterange((
        (date(2017, 1, 1), date(2017, 1, 1)),
        (date(2017, 1, 2), date(2017, 1, 2)),
        (date(2017, 1, 3), date(2017, 1, 3)),
    )) == (date(2017, 1, 4), date(2017, 1, 4))

    assert utils.predict_next_daterange((
        (date(2017, 1, 1), date(2017, 1, 1)),
        (date(2017, 1, 3), date(2017, 1, 3)),
        (date(2017, 1, 5), date(2017, 1, 5)),
    )) == (date(2017, 1, 7), date(2017, 1, 7))

    assert utils.predict_next_daterange((
        (datetime(2017, 1, 1, 10), datetime(2017, 1, 1, 12)),
        (datetime(2017, 1, 3, 10), datetime(2017, 1, 3, 12)),
        (datetime(2017, 1, 5, 10), datetime(2017, 1, 5, 12)),
    )) == (datetime(2017, 1, 7, 10), datetime(2017, 1, 7, 12))
