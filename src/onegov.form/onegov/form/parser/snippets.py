from onegov.form import _


class Snippets(object):

    fragments = (
        (_("Single line"), '___'),
        (_("Multi line"), '...'),
        (_("E-Mail"), '@@@'),
        (_("Website"), 'http://'),
        (_("E-Mail"), '@@@'),
        (_("Date"), 'YYYY.MM.DD'),
        (_("Time"), 'HH:MM'),
        (_("Date and time"), 'YYYY.MM.DD HH:MM'),
        (_("Multiple Choice"), (
            'Multiple Choice =\n',
            '    [ ] Choice 1\n',
            '    [ ] Choice 2\n',
            '    [ ] Choice 3\n',
        )),
        (_("Choice"), (
            'Choice =\n',
            '    (x) Option 1\n',
            '    ( ) Option 2\n',
            '    ( ) Option 3\n',
        )),
        (_("Image"), '*.jpg|*.png|*.gif'),
        (_("Document"), '*.pdf'),
        (_("Age"), '0..150'),
        (_("Percentage"), '0.00..100.00'),
        (_("IBAN"), '# iban'),
        (_("Swiss social security number"), '# ch.ssn'),
        (_("Swiss business identifier"), '# ch.uid'),
        (_("Swiss vat number"), '# ch.vat'),
    )

    def translated(self, request):
        for title, snippet in self.fragments:
            yield request.translate(title), snippet
