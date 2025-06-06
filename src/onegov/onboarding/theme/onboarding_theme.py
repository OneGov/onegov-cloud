from __future__ import annotations

from collections import OrderedDict
from onegov.foundation import BaseTheme
from onegov.core.utils import module_path


class OnboardingTheme(BaseTheme):
    name = 'onegov.onboarding.foundation'

    @property
    def post_imports(self) -> list[str]:
        return [
            'onboarding'
        ]

    @property
    def default_options(self) -> dict[str, str]:
        return OrderedDict((
            ('primary-color-ui', '#005BA1'),

            # base colors
            ('gray', '#e0e3e5'),
            ('black', '#0f0f0f'),
            ('blue', '#2575ed'),
            ('red', '#de2c3b'),
            ('yellow', '#ffc800'),
            ('orange', '#ffb100'),
            ('green', '#2c9f42'),
            ('white', '#fff'),
            ('gray-dark', '#b3b6b7'),
            ('black-dark', '#000'),
            ('blue-dark', '#1a52a5'),
            ('red-dark', '#b2232f'),
            ('yellow-dark', '#cca000'),
            ('orange-dark', '#d59200'),
            ('green-dark', '#237f35'),
            ('gray-light', '#f0f1f2'),
            ('black-light', '#363738'),
            ('blue-light', '#92baf6'),
            ('red-light', '#ef969d'),
            ('yellow-light', '#ffe480'),
            ('green-light', '#96cfa1'),
            # zurb overrides
            ('alert-color', '$red'),
            ('success-color', '$green'),
            ('warning-color', '$yellow'),
            ('info-color', '$blue'),

        ))

    @property
    def extra_search_paths(self) -> list[str]:
        return [module_path('onegov.onboarding.theme', 'styles')]
