from onegov.town import utils


def test_mark_images():
    html = "<p><img/></p><p></p>"
    assert utils.mark_images(html) == '<p class="has-img"><img></p><p></p>'

    html = "<p class='x'><img/></p><p></p>"
    assert utils.mark_images(html) == '<p class="x has-img"><img></p><p></p>'

    html = "<strong></strong>"
    assert utils.mark_images(html) == html

    html = "<a href=\"http://www.seantis.ch\"></a>"
    assert utils.mark_images(html) == html

    assert utils.mark_images('no html') == 'no html'
