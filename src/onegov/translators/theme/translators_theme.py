from onegov.core.utils import module_path
from onegov.foundation import BaseTheme


# options editable by the user
user_options = {
    'primary-color': '#1d487c',
}


class TranslatorAppTheme(BaseTheme):
    name = 'onegov.translators.foundation'

    @property
    def default_options(self):
        # Leave this empty, see below
        return {}

    @property
    def post_imports(self):
        return []

    @property
    def pre_imports(self):
        return []

    @property
    def extra_search_paths(self):
        return [module_path('onegov.translators.theme', 'styles')]
