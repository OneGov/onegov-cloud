from onegov.swissvotes import _


class Canton(object):
    """ A helper class to translate cantons. """

    def __init__(self, abbreviation):
        self.abbreviation = abbreviation

    def __eq__(self, other):
        return self.abbreviation == other.abbreviation

    @staticmethod
    def abbreviations():
        return (
            'ag', 'ai', 'ar', 'be', 'bl', 'bs', 'fr', 'ge', 'gl', 'gr', 'ju',
            'lu', 'ne', 'nw', 'ow', 'sg', 'sh', 'so', 'sz', 'tg', 'ti', 'ur',
            'vd', 'vs', 'zg', 'zh'
        )

    @property
    def label(self):
        return {
            'ag': _("canton-ag-label"),
            'ai': _("canton-ai-label"),
            'ar': _("canton-ar-label"),
            'be': _("canton-be-label"),
            'bl': _("canton-bl-label"),
            'bs': _("canton-bs-label"),
            'fr': _("canton-fr-label"),
            'ge': _("canton-ge-label"),
            'gl': _("canton-gl-label"),
            'gr': _("canton-gr-label"),
            'ju': _("canton-ju-label"),
            'lu': _("canton-lu-label"),
            'ne': _("canton-ne-label"),
            'nw': _("canton-nw-label"),
            'ow': _("canton-ow-label"),
            'sg': _("canton-sg-label"),
            'sh': _("canton-sh-label"),
            'so': _("canton-so-label"),
            'sz': _("canton-sz-label"),
            'tg': _("canton-tg-label"),
            'ti': _("canton-ti-label"),
            'ur': _("canton-ur-label"),
            'vd': _("canton-vd-label"),
            'vs': _("canton-vs-label"),
            'zg': _("canton-zg-label"),
            'zh': _("canton-zh-label"),
        }.get(self.abbreviation, self.abbreviation.upper())

    def html(self, request):
        return '<span title="{}">{}</span>'.format(
            request.translate(self.label),
            request.translate(self.abbreviation.upper())
        )
