from onegov.form import Form
from onegov.gazette.fields import HtmlField


def test_html_field():
    form = Form()
    field = HtmlField()
    field = field.bind(form, 'html')

    field.data = ''
    assert 'class="editor"' in field()
    assert field.validate(form)

    field.data = (
        '<h2><span class="">Lorem Ipsum</span></h2>'
        '<p>'
        '<span class="md-line md-end-block">'
        '<span class=""><em>Lorem</em></span>, <a href="xx">ipsum.</a>'
        '</span>'
        '<span class="md-line md-end-block"><script>XXXX</script></span>'
        '</p>'
    )

    field.validate(form)
    assert field.data == 'Lorem Ipsum<p><em>Lorem</em>, ipsum.XXXX</p>'
