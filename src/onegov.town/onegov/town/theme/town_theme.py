from collections import OrderedDict

from onegov.core.utils import module_path
from onegov.org.theme import OrgTheme


# options editable by the user
user_options = {
    'primary-color': '#006fba',
    'footer-height': '38px'
}


class TownTheme(OrgTheme):
    name = 'onegov.town.foundation'

    # don't touch this number, it's incremented using bumpversion, so every
    # release will automatically trigger a rebuild of the theme
    version = '1.11.0'

    @property
    def default_options(self):
        options = super().default_options
        options.update(OrderedDict((
            ('tile-image-1', '"../static/homepage-images/tile-1-small.jpg"'),
            ('tile-image-2', '"../static/homepage-images/tile-2-small.jpg"'),
            ('tile-image-3', '"../static/homepage-images/tile-3-small.jpg"'),
            ('tile-image-4', '"../static/homepage-images/tile-4-small.jpg"'),
            ('tile-image-5', '"../static/homepage-images/tile-5-small.jpg"'),
            ('tile-image-6', '"../static/homepage-images/tile-6-small.jpg"'),
        )))
        options.update(user_options)

        return options

    @property
    def post_imports(self):
        return super().post_imports + [
            'town'
        ]

    @property
    def extra_search_paths(self):
        base_paths = super().extra_search_paths
        return [module_path('onegov.town.theme', 'styles')] + base_paths
