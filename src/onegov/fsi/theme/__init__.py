from onegov.core.utils import module_path
from onegov.org.theme import OrgTheme


# options editable by the user
user_options = {
    'primary-color-ui': '#1d487c',
}


class FsiTheme(OrgTheme):
    name = 'onegov.fsi.theme'

    @property
    def post_imports(self) -> list[str]:
        return super().post_imports + [
            'fsi'
        ]

    @property
    def pre_imports(self) -> list[str]:
        return super().pre_imports + [
            'fsi-foundation-mods'
        ]

    @property
    def extra_search_paths(self) -> list[str]:
        base_paths = super().extra_search_paths
        return [module_path('onegov.fsi.theme', 'styles')] + base_paths
