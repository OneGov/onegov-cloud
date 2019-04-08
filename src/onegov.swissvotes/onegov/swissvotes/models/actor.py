from cached_property import cached_property
from onegov.swissvotes import _


class Actor(object):
    """ A helper class to translate political actors (parties, associations).

    Each actor consists of an abbreviation and a label, and might be rendered
    as a html span.

    """

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return self.name == other.name

    @staticmethod
    def parties():
        """ All known parties. """

        return (
            'bdp', 'csp', 'cvp', 'edu', 'evp', 'fdp', 'fps', 'glp', 'gps',
            'kvp', 'ldu', 'lega', 'lps', 'mcg', 'pda', 'poch', 'rep', 'sd',
            'sps', 'svp'
        )

    @staticmethod
    def associations():
        """ All known associations. """

        return (
            'acs', 'bpuk', 'eco', 'edk', 'endk', 'fdk', 'gdk', 'gem', 'kdk',
            'kkjpd', 'ldk', 'sav', 'sbk', 'sbv-usp', 'sgb', 'sgv', 'sodk',
            'ssv', 'tcs', 'travs', 'vcs', 'vdk', 'voev', 'vpod', 'vsa'
        )

    @cached_property
    def abbreviation(self):
        return {
            'acs': _("actor-acs-abbreviation"),
            'auns': _("actor-auns-abbreviation"),
            'bdp': _("actor-bdp-abbreviation"),
            'bpuk': _("actor-bpuk-abbreviation"),
            'csp': _("actor-csp-abbreviation"),
            'cvp-fr': _("actor-cvp-fr-abbreviation"),
            'cvp': _("actor-cvp-abbreviation"),
            'dem': _("actor-dem-abbreviation"),
            'dsp': _("actor-dsp-abbreviation"),
            'eco': _("actor-eco-abbreviation"),
            'edk': _("actor-edk-abbreviation"),
            'edu': _("actor-edu-abbreviation"),
            'endk': _("actor-endk-abbreviation"),
            'evp': _("actor-evp-abbreviation"),
            'fdk': _("actor-fdk-abbreviation"),
            'fdp-fr': _("actor-fdp-fr-abbreviation"),
            'fdp': _("actor-fdp-abbreviation"),
            'fmh': _("actor-fmh-abbreviation"),
            'fps': _("actor-fps-abbreviation"),
            'frap': _("actor-frap-abbreviation"),
            'ga': _("actor-ga-abbreviation"),
            'gdk': _("actor-gdk-abbreviation"),
            'gem': _("actor-gem-abbreviation"),
            'glp': _("actor-glp-abbreviation"),
            'gps': _("actor-gps-abbreviation"),
            'gsoa': _("actor-gsoa-abbreviation"),
            'hev': _("actor-hev-abbreviation"),
            'jbdp': _("actor-jbdp-abbreviation"),
            'jcvp': _("actor-jcvp-abbreviation"),
            'jevp': _("actor-jevp-abbreviation"),
            'jfdp': _("actor-jfdp-abbreviation"),
            'jgps': _("actor-jgps-abbreviation"),
            'jldu': _("actor-jldu-abbreviation"),
            'jlps': _("actor-jlps-abbreviation"),
            'jna': _("actor-jna-abbreviation"),
            'jpda': _("actor-jpda-abbreviation"),
            'jsd': _("actor-jsd-abbreviation"),
            'jsvp': _("actor-jsvp-abbreviation"),
            'juso': _("actor-juso-abbreviation"),
            'kdk': _("actor-kdk-abbreviation"),
            'kkjpd': _("actor-kkjpd-abbreviation"),
            'kvp': _("actor-kvp-abbreviation"),
            'ldk': _("actor-ldk-abbreviation"),
            'ldu': _("actor-ldu-abbreviation"),
            'lega': _("actor-lega-abbreviation"),
            'lps': _("actor-lps-abbreviation"),
            'mcg': _("actor-mcg-abbreviation"),
            'pda': _("actor-pda-abbreviation"),
            'poch': _("actor-poch-abbreviation"),
            'pps': _("actor-pps-abbreviation"),
            'psa': _("actor-psa-abbreviation"),
            'rep': _("actor-rep-abbreviation"),
            'sab': _("actor-sab-abbreviation"),
            'sante': _("actor-sante-abbreviation"),
            'sav': _("actor-sav-abbreviation"),
            'sbk': _("actor-sbk-abbreviation"),
            'sblv': _("actor-sblv-abbreviation"),
            'sbv-asb': _("actor-sbv-asb-abbreviation"),
            'sbv-usp': _("actor-sbv-usp-abbreviation"),
            'sd': _("actor-sd-abbreviation"),
            'seks': _("actor-seks-abbreviation"),
            'sgb': _("actor-sgb-abbreviation"),
            'sgv': _("actor-sgv-abbreviation"),
            'skos': _("actor-skos-abbreviation"),
            'sks': _("actor-sks-abbreviation"),
            'smv': _("actor-smv-abbreviation"),
            'sodk': _("actor-sodk-abbreviation"),
            'sol': _("actor-sol-abbreviation"),
            'sps': _("actor-sps-abbreviation"),
            'ssv': _("actor-ssv-abbreviation"),
            'svp': _("actor-svp-abbreviation"),
            'tcs': _("actor-tcs-abbreviation"),
            'travs': _("actor-travs-abbreviation"),
            'vcs': _("actor-vcs-abbreviation"),
            'vdk': _("actor-vdk-abbreviation"),
            'voev': _("actor-voev-abbreviation"),
            'vpod': _("actor-vpod-abbreviation"),
            'vsa': _("actor-vsa-abbreviation"),
        }.get(self.name, self.name)

    @cached_property
    def label(self):
        return {
            'acs': _("actor-acs-label"),
            'auns': _("actor-auns-label"),
            'bdp': _("actor-bdp-label"),
            'bpuk': _("actor-bpuk-label"),
            'csp': _("actor-csp-label"),
            'cvp-fr': _("actor-cvp-fr-label"),
            'cvp': _("actor-cvp-label"),
            'dem': _("actor-dem-label"),
            'dsp': _("actor-dsp-label"),
            'eco': _("actor-eco-label"),
            'edk': _("actor-edk-label"),
            'edu': _("actor-edu-label"),
            'endk': _("actor-endk-label"),
            'evp': _("actor-evp-label"),
            'fdk': _("actor-fdk-label"),
            'fdp-fr': _("actor-fdp-fr-label"),
            'fdp': _("actor-fdp-label"),
            'fmh': _("actor-fmh-label"),
            'fps': _("actor-fps-label"),
            'frap': _("actor-frap-label"),
            'ga': _("actor-ga-label"),
            'gdk': _("actor-gdk-label"),
            'gem': _("actor-gem-label"),
            'glp': _("actor-glp-label"),
            'gps': _("actor-gps-label"),
            'gsoa': _("actor-gsoa-label"),
            'hev': _("actor-hev-label"),
            'jbdp': _("actor-jbdp-label"),
            'jcvp': _("actor-jcvp-label"),
            'jevp': _("actor-jevp-label"),
            'jfdp': _("actor-jfdp-label"),
            'jgps': _("actor-jgps-label"),
            'jldu': _("actor-jldu-label"),
            'jlps': _("actor-jlps-label"),
            'jna': _("actor-jna-label"),
            'jpda': _("actor-jpda-label"),
            'jsd': _("actor-jsd-label"),
            'jsvp': _("actor-jsvp-label"),
            'juso': _("actor-juso-label"),
            'kdk': _("actor-kdk-label"),
            'kkjpd': _("actor-kkjpd-label"),
            'kvp': _("actor-kvp-label"),
            'ldk': _("actor-ldk-label"),
            'ldu': _("actor-ldu-label"),
            'lega': _("actor-lega-label"),
            'lps': _("actor-lps-label"),
            'mcg': _("actor-mcg-label"),
            'pda': _("actor-pda-label"),
            'poch': _("actor-poch-label"),
            'pps': _("actor-pps-label"),
            'psa': _("actor-psa-label"),
            'rep': _("actor-rep-label"),
            'sab': _("actor-sab-label"),
            'sante': _("actor-sante-label"),
            'sav': _("actor-sav-label"),
            'sbk': _("actor-sbk-label"),
            'sblv': _("actor-sblv-label"),
            'sbv-asb': _("actor-sbv-asb-label"),
            'sbv-usp': _("actor-sbv-usp-label"),
            'sd': _("actor-sd-label"),
            'seks': _("actor-seks-label"),
            'sgb': _("actor-sgb-label"),
            'sgv': _("actor-sgv-label"),
            'skos': _("actor-skos-label"),
            'sks': _("actor-sks-label"),
            'smv': _("actor-smv-label"),
            'sodk': _("actor-sodk-label"),
            'sol': _("actor-sol-label"),
            'sps': _("actor-sps-label"),
            'ssv': _("actor-ssv-label"),
            'svp': _("actor-svp-label"),
            'tcs': _("actor-tcs-label"),
            'travs': _("actor-travs-label"),
            'vcs': _("actor-vcs-label"),
            'vdk': _("actor-vdk-label"),
            'voev': _("actor-voev-label"),
            'vpod': _("actor-vpod-label"),
            'vsa': _("actor-vsa-label"),
        }.get(self.name, self.name)

    def html(self, request):
        return '<span title="{}">{}</span>'.format(
            request.translate(self.label),
            request.translate(self.abbreviation)
        )
