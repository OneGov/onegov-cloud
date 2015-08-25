from datetime import time
from onegov.town import utils


def test_mark_images():
    html = "<p><img/></p><p></p>"
    assert utils.mark_images(html) == '<p class="has-img"><img/></p><p/>'

    html = "<p class='x'><img/></p><p></p>"
    assert utils.mark_images(html) == '<p class="x has-img"><img/></p><p/>'

    assert utils.mark_images('no html') == 'no html'


def test_as_time():
    assert utils.as_time('00:00') == time(0, 0)
    assert utils.as_time('16:20') == time(16, 20)
    assert utils.as_time('24:00') == time(0, 0)
