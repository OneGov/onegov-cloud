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
        (_('Text'), '___'),
        (_('Multiline'), '...'),
        (_('E-Mail'), '@@@'),
        (_('Website'), 'http://'),
        (_('Video Link'), 'video-url'),

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

        (_('Numbers'), None),
        (_('Age'), '0..150'),
        (_('Percentage'), '0.00..100.00'),

        (_('Extended'), None),
        (_('IBAN'), '# iban'),
        (_('Swiss social security number'), '# ch.ssn'),
        (_('Swiss business identifier'), '# ch.uid'),
        (_('Swiss vat number'), '# ch.vat'),
        (_('Markdown'), '<markdown>')
    )

    def translated(
        self,
        request: 'CoreRequest'
    ) -> 'Iterator[tuple[str, str | None, TranslationString]]':
        for title, snippet in self.fragments:
            yield request.translate(title), snippet, title
