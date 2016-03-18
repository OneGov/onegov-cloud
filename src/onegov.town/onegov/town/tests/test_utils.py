from onegov.town import utils


def test_annotate_html():
    html = "<p><img/></p><p></p>"
    assert utils.annotate_html(html) == '<p class="has-img"><img></p><p></p>'

    html = "<p class='x'><img/></p><p></p>"
    assert utils.annotate_html(html) == '<p class="x has-img"><img></p><p></p>'

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
