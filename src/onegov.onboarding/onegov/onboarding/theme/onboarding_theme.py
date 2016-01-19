from collections import OrderedDict
from onegov.foundation import BaseTheme
from onegov.core.utils import module_path


class OnboardingTheme(BaseTheme):
    name = 'onegov.onboarding.foundation'

    # don't touch this number, it's incremented using bumpversion, so every
    # release will automatically trigger a rebuild of the theme
    version = '0.0.0'

    @property
    def post_imports(self):
        return [
            'onboarding'
        ]

    @property
    def default_options(self):
        return OrderedDict((
            ('primary-color', '#005FC1'),

            # base colors
            ('gray', '#e0e3e5'),
            ('black', '#0f0f0f'),
            ('blue', '#2575ed'),
            ('red', '#de2c3b'),
            ('yellow', '#ffc800'),
            ('orange', '#ffb100'),
            ('green', '#2c9f42'),
            ('white', '#fff'),

            # zurb overrides
            ('alert-color', '$red'),
            ('success-color', '$green'),
            ('warning-color', '$yellow'),
            ('info-color', '$blue'),
        ))

    @property
    def extra_search_paths(self):
        return [module_path('onegov.onboarding.theme', 'styles')]
