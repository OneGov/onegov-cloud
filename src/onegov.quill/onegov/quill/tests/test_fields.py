from onegov.form import Form
from onegov.quill.fields import QuillField


def test_html_field():
    form = Form()
    field = QuillField()
    field = field.bind(form, 'html')

    field.data = ''

    assert '<div class="quill-container"></div>' in field()
    assert field.validate(form)

    field.data = (
        '<h2><span class="">Lorem Ipsum</span></h2>'
        '<p>'
        '<span class="md-line md-end-block">'
        '<span class=""><em>Lorem</em></span>, <a href="xx">ipsum.</a>'
        '</span>'
        '<span class="md-line md-end-block"><script>XXXX</script></span>'
        '</p>'
        '<ul><li>1</li><li>2</li><li>3</li></ul>'
        '<ol><li>1</li><li>2</li><li>3</li></ol>'
    )

    field.validate(form)
    assert field.data == (
        'Lorem Ipsum<p><em>Lorem</em>, ipsum.XXXX</p>'
        '<ul><li>1</li><li>2</li><li>3</li></ul>'
        '<ol><li>1</li><li>2</li><li>3</li></ol>'
    )
