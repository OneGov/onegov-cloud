from onegov.form import Form
from onegov.gazette.fields import HtmlField
from onegov.gazette.fields import MultiCheckboxField
from onegov.gazette.fields import SelectField


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


def test_select_field():
    form = Form()
    field = SelectField(choices=(('a', 'b'),))
    field = field.bind(form, 'choice')

    field.data = ''
    assert 'class="chosen-select"' in field()


def test_multi_checkbox_field():
    form = Form()
    field = MultiCheckboxField(choices=(('a', 'b'),))
    field = field.bind(form, 'choice')

    field.data = ''
    assert 'data-expand-title="Show all"' in field()
    assert 'data-limit="10"' in field()
