from onegov.form import _


class Snippets(object):

    fragments = (
        (_("General"), None),
        (_("Title"), '#'),
        (_("Text"), '___'),
        (_("Multiline"), '...'),
        (_("E-Mail"), '@@@'),
        (_("Website"), 'http://'),

        (_("Date and time"), None),
        (_("Date"), 'YYYY.MM.DD'),
        (_("Time"), 'HH:MM'),
        (_("Date and time"), 'YYYY.MM.DD HH:MM'),

        (_("Choices"), None),
        (_("Choice"), (
            '\n'
            '    (x) A\n'
            '    ( ) B\n'
            '    ( ) C'
        )),
        (_("Multiple Choice"), (
            '\n'
            '    [ ] A\n'
            '    [ ] B\n'
            '    [ ] C'
        )),

        (_("Files"), None),
        (_("Image"), '*.jpg|*.png|*.gif'),
        (_("Document"), '*.pdf'),

        (_("Numbers"), None),
        (_("Age"), '0..150'),
        (_("Percentage"), '0.00..100.00'),

        (_("Extended"), None),
        (_("IBAN"), '# iban'),
        (_("Swiss social security number"), '# ch.ssn'),
        (_("Swiss business identifier"), '# ch.uid'),
        (_("Swiss vat number"), '# ch.vat'),
        (_("Markdown"), '<markdown>')
    )

    def translated(self, request):
        for title, snippet in self.fragments:
            yield request.translate(title), snippet
