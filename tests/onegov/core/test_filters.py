from __future__ import annotations

from io import StringIO
from onegov.core.filters import JsxFilter


def test_jsx_filter() -> None:
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
        '"use strict";'
        'var component=Rect.createClass({'
        'render:function render(){return React.createElement("div",null)}'
        '});'
    )
