import logging
log = logging.getLogger('onegov.gis')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from translationstring import TranslationStringFactory
_ = TranslationStringFactory('onegov.gis')  # noqa

from onegov.gis.forms import CoordinateForm
from onegov.gis.models import CoordinateMixin

__all__ = ['CoordinateForm', 'CoordinateMixin']
