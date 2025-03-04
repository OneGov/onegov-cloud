from __future__ import annotations

from onegov.form import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from translationstring import TranslationString
    from collections.abc import Iterator
    from onegov.core.request import CoreRequest


class Snippets:

    fragments = (
        (_('General'), None),
        (_('Title'), '#'),
        (_('E-Mail'), '@@@'),
        (_('Website'), 'http://'),
        (_('Video Link'), 'video-url'),

        (_('Text fields'), None),
        (_('Text'), '___'),
        (_('Limited text'), '___[50]'),
        (_('Multiline with optional number of rows'), '...[10]'),
        (_('Numbers-only textfield (regex)'), '___/^[0-9]+$'),

        (_('Comment'), None),
        (_('Example Comment'), '<<  >>'),

        (_('Date and time'), None),
        (_('Date'), 'YYYY.MM.DD'),
        (_('Time'), 'HH:MM'),
        (_('Date and time'), 'YYYY.MM.DD HH:MM'),

        (_('Choices'), None),
        (_('Choice'), (
            '\n'
            '    (x) A\n'
            '    ( ) B\n'
            '    ( ) C'
        )),
        (_('Multiple Choice'), (
            '\n'
            '    [ ] A\n'
            '    [ ] B\n'
            '    [ ] C'
        )),
        (_('Subfields depending on choice'), (
            '\n'
            '    [ ] Option A\n'
            '        Text A = ___\n'
            '    [ ] Option B\n'
            '        Text B = ___\n'
        )),

        (_('Files'), None),
        (_('Image'), '*.jpg|*.png|*.gif'),
        (_('Document'), '*.pdf'),
        (_('Documents (Multiple upload)'), '*.pdf (multiple)'),

        (_('Numbers'), None),
        (_('Age'), '0..150'),
        (_('Percentage'), '0.00..100.00'),
        (_('Amount with Price'), '0..30 (10 CHF)'),

        (_('Extended'), None),
        (_('IBAN'), '# iban'),
        (_('Swiss social security number'), '# ch.ssn'),
        (_('Swiss business identifier'), '# ch.uid'),
        (_('Swiss vat number'), '# ch.vat'),
        (_('Animal identification number (Microchip-Nr.)'), 'chip-nr'),
        (_('Password'), '***    '),
        (_('Markdown'), '<markdown>')
    )

    def translated(
        self,
        request: CoreRequest
    ) -> Iterator[tuple[str, str | None, TranslationString]]:
        for title, snippet in self.fragments:
            yield request.translate(title), snippet, title
