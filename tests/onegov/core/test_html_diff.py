from __future__ import annotations

import pytest

from onegov.core.html_diff import render_html_diff


@pytest.mark.parametrize('a,b,expected', [
    (
        'Foo <b>bar</b> baz',
        'Foo <i>bar</i> baz',
        '<div class="diff">Foo <i class="tagdiff_replaced">bar</i> baz</div>',
    ),
    (
        'Foo bar baz',
        'Foo baz',
        '<div class="diff">Foo <del>bar</del> baz</div>',
    ),
    (
        'Foo baz',
        'Foo blah baz',
        '<div class="diff">Foo <ins>blah</ins> baz</div>',
    ),
    # NOTE: It's a little weird that insertion/deletion order flips
    #       between added/removed tags, but there's no easy way to
    #       fix this with the current implementation.
    (
        'Foo baz',
        'Foo <b>baz</b>',
        '<div class="diff">Foo <del>baz</del><b><ins>baz</ins></b></div>',
    ),
    (
        'Foo <b>baz</b>',
        'Foo baz',
        '<div class="diff">Foo <ins>baz</ins><b><del>baz</del></b></div>',
    ),
])
def test_html_diff(a: str, b: str, expected: str) -> None:
    assert render_html_diff(a, b) == expected
