import logging
log = logging.getLogger('onegov.onboarding')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from translationstring import TranslationStringFactory
_ = TranslationStringFactory('onegov.onboarding')  # noqa

from onegov.oneboarding import OnboardingApp

__all__ = ['_', 'log', 'OnboardingApp']
