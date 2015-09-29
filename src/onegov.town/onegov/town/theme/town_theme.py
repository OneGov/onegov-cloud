from collections import OrderedDict

from onegov.foundation import BaseTheme
from onegov.core.utils import module_path


# options editable by the user
user_options = {
    'primary-color': '#006fba',
    'footer-height': '200px'
}


class TownTheme(BaseTheme):
    name = 'onegov.town.foundation'

    # don't touch this number, it's incremented using bumpversion, so every
    # release will automatically trigger a rebuild of the theme
    version = '0.6.2'

    @property
    def default_options(self):
        options = OrderedDict((
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
            ('gray-pastel', '#f7f8f8'),
            ('black-pastel', '#dadada'),
            ('blue-pastel', '#d3e3fb'),
            ('red-pastel', '#f8d5d8'),
            ('yellow-pastel', '#fff4cc'),
            ('green-pastel', '#d4ecd8'),

            # zurb overrides
            ('alert-color', '$red'),
            ('success-color', '$green'),
            ('warning-color', '$yellow'),
            ('info-color', '$blue'),
            ('callout-panel-bg', '$yellow-light'),
            ('callout-panel-border-color', '$yellow'),
            ('top-bar-border-size', '0.3rem'),
            ('bottom-links-color', '#777'),
            ('bottom-links-size', '0.8rem'),
            ('topbar-bg-color', '$gray-pastel'),
            ('topbar-link-bg-hover', '$gray'),
            ('topbar-link-color', '#312f2e'),
            ('topbar-link-color-hover', '#312f2e'),
            ('topbar-link-color-active', '#312f2e'),
            ('topbar-link-color-active-hover', '#312f2e'),
            ('topbar-link-weight', 'bold'),
            ('topbar-menu-link-color', '#312f2e'),
            ('topbar-menu-icon-color', '#312f2e'),
            ('topbar-dropdown-bg', '$gray-pastel'),
            ('side-nav-font-weight-active', 'bold'),
            ('side-nav-padding', '0'),
            ('side-nav-link-padding', 'rem-calc(0 14)'),
            ('crumb-bg', '#fff'),
            ('crumb-border-size', '0'),
            ('header-line-height', '1.25'),
            ('sub-nav-padding', '.25rem'),
            ('table-border-style', 'none'),

            # custom
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
    def post_imports(self):
        return [
            'town'
        ]

    @property
    def extra_search_paths(self):
        return [module_path('onegov.town.theme', 'styles')]
