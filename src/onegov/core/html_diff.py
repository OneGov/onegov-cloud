"""
htmldiff
========

Diffs HTML fragments.  Nice to show what changed between two revisions
of a document for an arbitrary user.

Examples:
.. code-block:: pycon

    >>> from htmldiff import render_html_diff

    >>> render_html_diff('Foo <b>bar</b> baz', 'Foo <i>bar</i> baz')
    '<div class="diff">Foo <i class="tagdiff_replaced">bar</i> baz</div>'

    >>> render_html_diff('Foo bar baz', 'Foo baz')
    '<div class="diff">Foo <del>bar</del> baz</div>'

    >>> render_html_diff('Foo baz', 'Foo blah baz')
    '<div class="diff">Foo <ins>blah</ins> baz</div>'

:copyright: (c) 2011 by Armin Ronacher
:license: BSD
"""
from __future__ import annotations

import re
from contextlib import contextmanager
from difflib import SequenceMatcher
from itertools import chain, zip_longest

import html5lib
from genshi.core import Stream, QName, Attrs, START, END, TEXT  # type:ignore
from genshi.input import ET  # type:ignore[import-untyped]
from markupsafe import Markup


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from genshi.core import StreamEventKind
    from typing import TypeAlias

    Position: TypeAlias = tuple[str | None, int, int]
    StreamEvent: TypeAlias = tuple[StreamEventKind, Any, Position]


_leading_space_re = re.compile(r'^(\s+)')
_diff_split_re = re.compile(r'(\s+)')


def diff_genshi_stream(old_stream: Stream, new_stream: Stream) -> Stream:
    """Renders a creole diff for two texts."""
    differ = StreamDiffer(old_stream, new_stream)
    return differ.get_diff_stream()


def render_html_diff(
    old: str,
    new: str,
    wrapper_element: str = 'div',
    wrapper_class: str = 'diff'
) -> Markup:
    """Renders the diff between two HTML fragments."""
    old_stream = parse_html(old, wrapper_element, wrapper_class)
    new_stream = parse_html(new, wrapper_element, wrapper_class)
    rv = diff_genshi_stream(old_stream, new_stream)
    return Markup(rv.render('html', encoding=None))  # nosec: B704


def parse_html(
    html: str,
    wrapper_element: str = 'div',
    wrapper_class: str = 'diff'
) -> ET:
    """Parse an HTML fragment into a Genshi stream."""
    builder = html5lib.getTreeBuilder('etree')
    parser = html5lib.HTMLParser(tree=builder)
    tree = parser.parseFragment(html)
    tree.tag = wrapper_element
    if wrapper_class is not None:
        tree.set('class', wrapper_class)
    return ET(tree)


class StreamDiffer:
    """A class that can diff a stream of Genshi events. It will inject
    ``<ins>`` and ``<del>`` tags into the stream. It probably breaks
    in very ugly ways if you pass a random Genshi stream to it. I'm
    not exactly sure if it's correct what creoleparser is doing here,
    but it appears that it's not using a namespace. That's fine with me
    so the tags the `StreamDiffer` adds are also unnamespaced.
    """

    _old: list[StreamEvent]
    _new: list[StreamEvent]
    _result: list[StreamEvent]
    _stack: list[str]
    _context: str | None

    def __init__(self, old_stream: ET, new_stream: ET):
        self._old = list(old_stream)
        self._new = list(new_stream)
        # FIXME: We should probably switch to a hasattr check
        self._result = None  # type:ignore[assignment]
        self._stack = []
        self._context = None

    @contextmanager
    def context(self, kind: str | None) -> Iterator[None]:
        old_context = self._context
        self._context = kind
        try:
            yield
        finally:
            self._context = old_context

    def inject_class(self, attrs: Attrs, classname: str) -> Attrs:
        cls = attrs.get('class')
        attrs |= [(QName('class'), cls and cls + ' ' + classname or classname)]
        return attrs

    def append(
        self,
        type: StreamEventKind,
        data: Any,
        pos: Position
    ) -> None:
        self._result.append((type, data, pos))

    def text_split(self, text: str) -> list[str]:
        worditer = chain([''], _diff_split_re.split(text))
        return [x + next(worditer) for x in worditer]

    def cut_leading_space(self, s: str) -> tuple[str, str]:
        match = _leading_space_re.match(s)
        if match is None:
            return '', s
        return match.group(), s[match.end():]

    def mark_text(self, pos: Position, text: str, tag: str) -> None:
        ws, text = self.cut_leading_space(text)
        tag = QName(tag)
        if ws:
            self.append(TEXT, ws, pos)
        self.append(START, (tag, Attrs()), pos)
        self.append(TEXT, text, pos)
        self.append(END, tag, pos)

    def diff_text(self, pos: Position, old_text: str, new_text: str) -> None:
        old = self.text_split(old_text)
        new = self.text_split(new_text)
        matcher = SequenceMatcher(None, old, new)

        # FIXME: This function is too simple to be worth it, get rid of it
        def wrap(tag: str, words: list[str]) -> None:
            self.mark_text(pos, ''.join(words), tag)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                wrap('del', old[i1:i2])
                wrap('ins', new[j1:j2])
            elif tag == 'delete':
                wrap('del', old[i1:i2])
            elif tag == 'insert':
                wrap('ins', new[j1:j2])
            else:
                self.append(TEXT, ''.join(old[i1:i2]), pos)

    def replace(
        self,
        old_start: int,
        old_end: int,
        new_start: int,
        new_end: int
    ) -> None:

        old = self._old[old_start:old_end]
        new = self._new[new_start:new_end]

        for idx, (old_event, new_event) in enumerate(zip_longest(old, new)):
            if old_event is None:
                self.insert(new_start + idx, new_end + idx)
                break
            elif new_event is None:
                self.delete(old_start + idx, old_end + idx)
                break

            # the best case. We're in both cases dealing with the same
            # event type. This is the easiest because all routines we
            # have can deal with that.
            if old_event[0] == new_event[0]:
                type = old_event[0]
                # start tags are easy. handle them first.
                if type == START:
                    _, (tag, attrs), pos = new_event
                    self.enter_mark_replaced(pos, tag, attrs)
                # ends in replacements are a bit tricker, we try to
                # leave the new one first, then the old one. One
                # should succeed.
                elif type == END:
                    _, tag, pos = new_event
                    if not self.leave(pos, tag):
                        self.leave(pos, old_event[1])
                # replaced text is internally diffed again
                elif type == TEXT:
                    _, new_text, pos = new_event
                    self.diff_text(pos, old_event[1], new_text)
                # for all other stuff we ignore the old event
                else:
                    self.append(*new_event)

            # ob boy, now the ugly stuff starts. Let's handle the
            # easy one first. If the old event was text and the
            # new one is the start or end of a tag, we just process
            # both of them. The text is deleted, the rest is handled.
            elif old_event[0] == TEXT and new_event[0] in (START, END):
                _, text, pos = old_event
                self.mark_text(pos, text, 'del')
                type, data, pos = new_event
                if type == START:
                    self.enter(pos, *data)
                else:
                    self.leave(pos, data)

            # now the case that the old stream opened or closed a tag
            # that went away in the new one. In this case we just
            # insert the text and totally ignore the fact that we had
            # a tag. There is no way this could be rendered in a sane
            # way.
            elif old_event[0] in (START, END) and new_event[0] == TEXT:
                _, text, pos = new_event
                self.mark_text(pos, text, 'ins')

            # meh. no idea how to handle that, let's just say nothing
            # happened.
            else:
                pass

    def delete(self, start: int, end: int) -> None:
        with self.context('del'):
            self.block_process(self._old[start:end])

    def insert(self, start: int, end: int) -> None:
        with self.context('ins'):
            self.block_process(self._new[start:end])

    def unchanged(self, start: int, end: int) -> None:
        with self.context(None):
            self.block_process(self._old[start:end])

    def enter(self, pos: Any, tag: Any, attrs: dict[str, Any]) -> None:
        self._stack.append(tag)
        self.append(START, (tag, attrs), pos)

    def enter_mark_replaced(
        self,
        pos: Position,
        tag: str,
        attrs: Attrs
    ) -> None:
        attrs = self.inject_class(attrs, 'tagdiff_replaced')
        self._stack.append(tag)
        self.append(START, (tag, attrs), pos)

    def leave(self, pos: Position, tag: str) -> bool:
        if not self._stack:
            return False
        if tag == self._stack[-1]:
            self.append(END, tag, pos)
            self._stack.pop()
            return True
        return False

    def leave_all(self) -> None:
        if self._stack:
            last_pos = (self._new or self._old)[-1][2]
            for tag in reversed(self._stack):
                self.append(END, tag, last_pos)
        del self._stack[:]

    def block_process(self, events: list[StreamEvent]) -> None:
        for event in events:
            type, data, pos = event
            if type == START:
                self.enter(pos, *data)
            elif type == END:
                self.leave(pos, data)
            elif type == TEXT:
                if self._context is not None and data.strip():
                    tag = QName(self._context)
                    self.append(START, (QName(tag), Attrs()), pos)
                    self.append(type, data, pos)
                    self.append(END, tag, pos)
                else:
                    self.append(type, data, pos)
            else:
                self.append(type, data, pos)

    def process(self) -> None:
        self._result = []
        matcher = SequenceMatcher(None, self._old, self._new)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                self.replace(i1, i2, j1, j2)
            elif tag == 'delete':
                self.delete(i1, i2)
            elif tag == 'insert':
                self.insert(j1, j2)
            else:
                self.unchanged(i1, i2)
        self.leave_all()

    def get_diff_stream(self) -> Stream:
        # FIXME: We should probably switch to a hasattr check
        if self._result is None:
            self.process()  # type:ignore[unreachable]
        return Stream(self._result)
