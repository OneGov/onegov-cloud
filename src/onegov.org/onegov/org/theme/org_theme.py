from collections import OrderedDict

from onegov.foundation import BaseTheme
from onegov.core.utils import module_path


# options editable by the user
user_options = {
    'primary-color': '#006fba',
    'footer-height': '38px'
}


class OrgTheme(BaseTheme):
    name = 'onegov.org.foundation'

    # don't touch this number, it's incremented using bumpversion, so every
    # release will automatically trigger a rebuild of the theme
    version = '0.30.1'

    @property
    def default_options(self):
        options = OrderedDict((
            # tile images
            ('tile-image-1', '"../static/homepage-images/tile-1-small.jpg"'),
            ('tile-image-2', '"../static/homepage-images/tile-2-small.jpg"'),
            ('tile-image-3', '"../static/homepage-images/tile-3-small.jpg"'),
            ('tile-image-4', '"../static/homepage-images/tile-4-small.jpg"'),
            ('tile-image-5', '"../static/homepage-images/tile-5-small.jpg"'),
            ('tile-image-6', '"../static/homepage-images/tile-6-small.jpg"'),
        ))
        options.update(user_options)

        return options

    @property
    def foundation_components(self):
        return (
            'grid',
            'alert-boxes',
            'block-grid',
            'breadcrumbs',
            'button-groups',
            'buttons',
            'dropdown',
            'dropdown-buttons',
            'forms',
            'inline-lists',
            'labels',
            'orbit',
            'pagination',
            'panels',
            'progress-bars',
            'reveal',
            'side-nav',
            'split-buttons',
            'sub-nav',
            'tables',
            'thumbs',
            'tooltips',
            'top-bar',
            'type',
            'visibility',
        )

    @property
    def pre_imports(self):
        return [
            'foundation-mods',
        ]

    @property
    def post_imports(self):
        return [
            'org'
        ]

    @property
    def extra_search_paths(self):
        return [module_path('onegov.org.theme', 'styles')]
