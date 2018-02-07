from onegov.form import Form
from onegov.quill.widgets import QuillInput
from onegov.quill.fields import QuillField


def test_widget_initalization():
    input = QuillInput()
    assert input.formats == ["'bold'", "'italic'", "'list'"]
    assert input.toolbar == [
        "'bold'", "'italic'", "{'list': 'ordered'}", "{'list': 'bullet'}"
    ]

    input = QuillInput(tags=['strong', 'ul'])
    assert input.formats == ["'bold'", "'list'"]
    assert input.toolbar == ["'bold'", "{'list': 'bullet'}"]

    input = QuillInput(tags=['em', 'ol'])
    assert input.formats == ["'italic'", "'list'"]
    assert input.toolbar == ["'italic'", "{'list': 'ordered'}"]

    input = QuillInput(tags=['strong'])
    assert input.formats == ["'bold'"]
    assert input.toolbar == ["'bold'"]

    input = QuillInput(tags=['a', 'i'])
    assert input.formats == []
    assert input.toolbar == []


def test_widget_render():
    form = Form()
    field = QuillField()
    field = field.bind(form, 'html')
    field.data = 'xxx'

    input = QuillInput()
    text = input(field)
    assert input.container_id in text
    assert input.input_id in text
    assert "['bold', 'italic', 'list']" in text
    assert (
        "['bold', 'italic', {'list': 'ordered'}, {'list': 'bullet'}]}"
    ) in text

    input = QuillInput(tags=['em', 'ul'])
    text = input(field)
    assert input.container_id in text
    assert input.input_id in text
    assert "['italic', 'list']" in text
    assert "['italic', {'list': 'bullet'}]}" in text
