from onegov.core.utils import module_path
from onegov.foundation6 import BaseTheme


class RedesignTheme(BaseTheme):
    name = 'onegov.test.foundation6'

    @property
    def extra_search_paths(self):
        return [
            module_path('onegov.redesign_test.theme', 'styles'),
        ]

    @property
    def pre_imports(self):
        return ['foundation-mods']

    @property
    def post_imports(self):
        return [
            'redesign',
        ]
