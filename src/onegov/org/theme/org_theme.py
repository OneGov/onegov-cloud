from collections import OrderedDict

from onegov.foundation import BaseTheme
from onegov.core.utils import module_path


# options editable by the user
user_options = {
    'primary-color': '#006fba',
}


class OrgTheme(BaseTheme):
    name = 'onegov.org.foundation'

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
            'accordion',
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
            'switches',
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
