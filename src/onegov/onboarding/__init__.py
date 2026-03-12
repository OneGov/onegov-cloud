from __future__ import annotations

import logging
log = logging.getLogger('onegov.onboarding')
log.addHandler(logging.NullHandler())

from onegov.onboarding.i18n import _

from onegov.onboarding.app import OnboardingApp

__all__ = ('_', 'log', 'OnboardingApp')
