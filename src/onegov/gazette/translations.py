""" Contains a list of manual translations. Those are usually messages that
exist in external packages which provide no translations.

"""

from onegov.gazette import _

# FIXME: WTForms does ship with translations now, so we might consider just
#        loading those in addition to our own
# messages defined in wtforms
_("CSRF token expired")
