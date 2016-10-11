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
    version = '0.0.13'

    @property
    def default_options(self):
        options = OrderedDict((
            # base colors
            ('black', '#0f0f0f'),
            ('black-dark', '#000'),
            ('black-light', '#363738'),
            ('black-pastel', '#dadada'),
            ('blue', '#2575ed'),
            ('blue-dark', '#1a52a5'),
            ('blue-light', '#92baf6'),
            ('blue-pastel', '#d3e3fb'),
            ('gray', '#e0e3e5'),
            ('gray-dark', '#b3b6b7'),
            ('gray-light', '#f0f1f2'),
            ('gray-pastel', '#f7f8f8'),
            ('green', '#2c9f42'),
            ('green-dark', '#237f35'),
            ('green-light', '#96cfa1'),
            ('green-pastel', '#d4ecd8'),
            ('orange', '#ffb100'),
            ('orange-dark', '#d59200'),
            ('red', '#de2c3b'),
            ('red-dark', '#b2232f'),
            ('red-light', '#ef969d'),
            ('red-pastel', '#f8d5d8'),
            ('white', '#fff'),
            ('yellow', '#ffc800'),
            ('yellow-dark', '#cca000'),
            ('yellow-light', '#ffe480'),
            ('yellow-pastel', '#fff4cc'),

            # zurb overrides
            ('alert-color', '$red'),
            ('bottom-links-color', '#777'),
            ('bottom-links-size', '0.8rem'),
            ('callout-panel-bg', '$yellow-light'),
            ('callout-panel-border-color', '$yellow'),
            ('crumb-bg', '#fff'),
            ('crumb-border-size', '0'),
            ('header-line-height', '1.25'),
            ('include-print-styles', 'false'),
            ('info-color', '$blue'),
            ('side-nav-font-weight-active', 'bold'),
            ('side-nav-link-padding', 'rem-calc(0 14)'),
            ('side-nav-padding', '0'),
            ('sub-nav-padding', '.25rem'),
            ('success-color', '$green'),
            ('table-border-style', 'none'),
            ('thumb-border-width', '0'),
            ('thumb-box-shadow', '0 0 0 2px rgba($black,.1)'),
            ('thumb-box-shadow-hover', '0 0 0 2px rgba($black,.3)'),
            ('top-bar-border-size', '0.3rem'),
            ('topbar-bg-color', '$gray-pastel'),
            ('topbar-dropdown-bg', '$gray-pastel'),
            ('topbar-link-bg-hover', '$gray'),
            ('topbar-link-color', '#312f2e'),
            ('topbar-link-color-active', '#312f2e'),
            ('topbar-link-color-active-hover', '#312f2e'),
            ('topbar-link-color-hover', '#312f2e'),
            ('topbar-link-weight', 'bold'),
            ('topbar-menu-icon-color', '#312f2e'),
            ('topbar-menu-link-color', '#312f2e'),
            ('warning-color', '$orange'),

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
    def pre_imports(self):
        return [
            'foundation-mods'
        ]

    @property
    def post_imports(self):
        return [
            'org'
        ]

    @property
    def extra_search_paths(self):
        return [module_path('onegov.org.theme', 'styles')]
