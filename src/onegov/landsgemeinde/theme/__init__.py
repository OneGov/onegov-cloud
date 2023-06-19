from onegov.core.utils import module_path
from onegov.town6.theme import TownTheme


class LandsgemeindeTheme(TownTheme):
    name = 'onegov.landsgemeinde.theme'

    @property
    def post_imports(self):
        return super().post_imports + [
            'landsgemeinde'
        ]

    @property
    def extra_search_paths(self):
        base_paths = super().extra_search_paths
        return [
            module_path('onegov.landsgemeinde.theme', 'styles')
        ] + base_paths
