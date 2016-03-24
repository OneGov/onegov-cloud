import logging
log = logging.getLogger('onegov.gis')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from translationstring import TranslationStringFactory
_ = TranslationStringFactory('onegov.gis')  # noqa

from onegov.gis.forms import MapPointForm
from onegov.gis.models import MapPointMixin

__all__ = ['MapPointForm', 'MapPointMixin']
