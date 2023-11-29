import os

from onegov.foundation6 import BaseTheme
from onegov.core.utils import module_path

HELVETICA = '"Helvetica Neue", Helvetica, Roboto, Arial, sans-serif !default'
ARIAL = 'Arial, sans-serif !default'
VERDANA = 'Verdana, Geneva, sans-serif !default'
COURIER_NEW = '"Courier New", Courier, monospace !default'     # monospace
ROBOTO_CONDENSED = '"Roboto Condensed", sans-serif !default'
MERRIWEATHER = 'Merriweather, sans-serif !default'

# "Merriweather","Helvetica Neue",Helvetica,Roboto,Arial,sans-serif
# options editable by the user
user_options = {
    'primary-color-ui': '#006fba',
    'body-font-family-ui': MERRIWEATHER,
    'header-font-family-ui': ROBOTO_CONDENSED
}

default_font_families = {
    'Roboto Condensed': ROBOTO_CONDENSED,
    'Helvetica': HELVETICA,
    'Arial': ARIAL,
    'Verdana': VERDANA,
    'Courier New': COURIER_NEW,
}


class TownTheme(BaseTheme):
    name = 'onegov.town6.foundation'

    _force_compile = False
    use_flex = True
    include_motion_ui = True

    @property
    def default_options(self):
        return user_options

    @property
    def foundation_styles(self):
        return 'global-styles', 'forms', 'typography'

    @property
    def foundation_components(self):
        return (
            'button',
            'button-group',
            'close-button',
            'label',
            # 'progress-bar',
            # 'slider',
            # 'switch',
            'table',
            # 'badge',
            'breadcrumbs',
            'callout',
            'card',
            'dropdown',
            'pagination',
            'tooltip',
            'accordion',
            'media-object',
            'orbit',
            'responsive-embed',
            'tabs',
            'thumbnail',
            'menu',
            'menu-icon',
            'accordion-menu',
            'drilldown-menu',
            'dropdown-menu',
            'off-canvas',
            'reveal',
            'sticky',
            'title-bar',
            'top-bar',
        )

    @property
    def pre_imports(self):
        imports = [
            'foundation-mods',
        ]
        for font_family in self.additional_font_families:
            imports.append(font_family)
        return imports

    @property
    def post_imports(self):
        """Our scss code split into various files"""
        return [
            'custom_mixins',
            'typography',
            'header',
            'org',
            'sortable',
            'sidebars',
            'forms',
            'formcode',
            'panels',
            'sliders',
            'org-settings',
            'helpers',
            'footer',
            'chosen',
            'news',
            'events',
            'homepage-tiles',
            'tickets',
            'user',
            'timeline',
            'upload',
            'files',
            'publication_signature',
            'image-grid',
            'widgets',
            'popup',
            'fullcalendar',
            'alert',
            'redactor',
            'directories',
            'daypicker',
            'payment',
            'person',
            'newsletter',
            'search',
            'hints',
            'allocations',
            'homepage',
            'progress_indicator',
            'healthcheck',
            'qrcode',
            'leaflet',
            'tags',
            'chat'
        ]

    @property
    def extra_search_paths(self):
        return super().extra_search_paths + [
            module_path('onegov.town6.theme', 'styles'),
            self.font_search_path
        ]

    @property
    def font_search_path(self):
        """ Load fonts of the current theme folder and ignore fonts from
        parent applications if OrgTheme is inherited. """
        module = self.name.replace('foundation', 'theme')
        return module_path(module, 'fonts')

    @property
    def font_families(self):
        families = default_font_families.copy()
        families.update(self.additional_font_families)
        return families

    @property
    def additional_font_families(self):
        """ Returns the filenames as they are to use as label in the settings
        as well as to construct the font-family string.
        Only sans-serif fonts are supported by now.
        """
        if not os.path.exists(self.font_search_path):
            return {}

        def fn(n):
            return n.split('.')

        return {
            fn(n)[0]: f'"{fn(n)[0]}", {HELVETICA}' for n in os.listdir(
                self.font_search_path) if fn(n)[1] in ('css', 'scss')
        }
