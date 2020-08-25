from onegov.core.utils import module_path
from onegov.org.theme import OrgTheme


# options editable by the user
user_options = {
    'primary-color': '#1d487c',
}


class TranslatorDirectoryTheme(OrgTheme):
    name = 'onegov.translator_directory.theme'

    @property
    def post_imports(self):
        return super().post_imports + [
            'translator_directory'
        ]

    @property
    def extra_search_paths(self):
        base_paths = super().extra_search_paths
        return [
           module_path('onegov.translator_directory.theme', 'styles')
        ] + base_paths
