from onegov.core.compat import StringIO
from onegov.core.jsx import JsxFilter


def test_jsx_filter():
    filter = JsxFilter()
    filter.setup()

    input = StringIO((
        'var component = Rect.createClass({'
        'render: function() { return <div />; }'
        '});'
    ))
    output = StringIO()
    filter.input(input, output)

    output.seek(0)
    assert output.read() == (
        'var component = Rect.createClass({'
        'render: function() { return React.createElement("div", null); }'
        '});'
    )
