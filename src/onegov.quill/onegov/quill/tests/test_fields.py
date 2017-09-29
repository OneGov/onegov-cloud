from onegov.form import Form
from onegov.quill.fields import QuillField


def test_field_clean():
    form = Form()

    field = QuillField(tags=[])
    field = field.bind(form, 'html')
    field.data = None
    assert field.validate(form)

    test_data = """
        <h2>
            <span class="">A<strong>B</strong><b>C</b></span>
        </h2>
        <p>
            <span class="md-line md-end-block">
                <span class=""><em>D</em><i>E</i></span><a href="xx">F</a>
                <br>
            </span>
            <span class="md-line md-end-block">
                <script>XXXX</script>
            </span>
        </p>
            <ul>
                <li>1</li>
                <li>2</li>
                <li>3</li>
            </ul>
            <ol>
                <li>1</li>
                <li>2</li>
                <li>3</li>
            </ol>
    """

    field = QuillField(tags=[])
    field = field.bind(form, 'html')
    field.data = test_data
    assert field.validate(form)
    assert field.data.replace(' ', '').replace('\n', '') == (
        'ABC<p>DEF<br>XXXX</p>123123'
    )

    field = QuillField(tags=['strong'])
    field = field.bind(form, 'html')
    field.data = test_data
    assert field.validate(form)
    assert field.data.replace(' ', '').replace('\n', '') == (
        'A<strong>B</strong>C<p>DEF<br>XXXX</p>123123'
    )

    field = QuillField(tags=['em', 'ol', 'ul'])
    field = field.bind(form, 'html')
    field.data = test_data
    assert field.validate(form)
    assert field.data.replace(' ', '').replace('\n', '') == (
        'ABC<p><em>D</em>EF<br>XXXX</p>'
        '<ul><li>1</li><li>2</li><li>3</li></ul>'
        '<ol><li>1</li><li>2</li><li>3</li></ol>'
    )

    field = QuillField(tags=['ol'])
    field = field.bind(form, 'html')
    field.data = test_data
    assert field.validate(form)
    assert field.data.replace(' ', '').replace('\n', '') == (
        'ABC<p>DEF<br>XXXX</p>'
        '<li>1</li><li>2</li><li>3</li>'
        '<ol><li>1</li><li>2</li><li>3</li></ol>'
    )

    field = QuillField(tags=['strong', 'ul'])
    field = field.bind(form, 'html')
    field.data = test_data
    assert field.validate(form)
    assert field.data.replace(' ', '').replace('\n', '') == (
        'A<strong>B</strong>C<p>DEF<br>XXXX</p>'
        '<ul><li>1</li><li>2</li><li>3</li></ul>'
        '<li>1</li><li>2</li><li>3</li>'
    )

    field = QuillField()
    field = field.bind(form, 'html')
    field.data = test_data
    assert field.validate(form)
    assert field.data.replace(' ', '').replace('\n', '') == (
        'A<strong>B</strong>C<p><em>D</em>EF<br>XXXX</p>'
        '<ul><li>1</li><li>2</li><li>3</li></ul>'
        '<ol><li>1</li><li>2</li><li>3</li></ol>'
    )

    field = QuillField(tags=['a', 'i', 'b'])
    field = field.bind(form, 'html')
    field.data = test_data
    assert field.validate(form)
    assert field.data.replace(' ', '').replace('\n', '') == (
        'ABC<p>DEF<br>XXXX</p>123123'
    )
