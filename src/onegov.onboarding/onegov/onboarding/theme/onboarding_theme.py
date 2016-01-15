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
        return {}

    @property
    def extra_search_paths(self):
        return [module_path('onegov.onboarding.theme', 'styles')]
