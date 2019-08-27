from onegov.swissvotes import _


class Region(object):
    """ A helper class to translate geographical cantons.

    Each canton consists of an abbreviation and a label, and might be rendered
    as a html span.

    """

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return self.name == other.name

    @staticmethod
    def cantons():
        """ All known cantons. """

        return (
            'ag', 'ai', 'ar', 'be', 'bl', 'bs', 'fr', 'ge', 'gl', 'gr', 'ju',
            'lu', 'ne', 'nw', 'ow', 'sg', 'sh', 'so', 'sz', 'tg', 'ti', 'ur',
            'vd', 'vs', 'zg', 'zh'
        )

    @property
    def abbreviation(self):
        return {
            'ag': 'AG',
            'ai': 'AI',
            'ar': 'AR',
            'be': 'BE',
            'bl': 'BL',
            'bs': 'BS',
            'fr': 'FR',
            'ge': 'GE',
            'gl': 'GL',
            'gr': 'GR',
            'ju': 'JU',
            'lu': 'LU',
            'ne': 'NE',
            'nw': 'NW',
            'ow': 'OW',
            'sg': 'SG',
            'sh': 'SH',
            'so': 'SO',
            'sz': 'SZ',
            'tg': 'TG',
            'ti': 'TI',
            'ur': 'UR',
            'vd': 'VD',
            'vs': 'VS',
            'zg': 'ZG',
            'zh': 'ZH',
            'ch': 'CH',
            'vso': 'VSo',
            'vsr': 'VSr',
        }.get(self.name, self.name)

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
            'ch': _("canton-ch-label"),
            'vso': _("canton-vso-label"),
            'vsr': _("canton-vsr-label"),
        }.get(self.name, self.name)

    def html(self, request):
        return '<span title="{}">{}</span>'.format(
            request.translate(self.label),
            request.translate(self.abbreviation)
        )
