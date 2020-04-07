import os
from collections import OrderedDict

from onegov.foundation import BaseTheme
from onegov.core.utils import module_path

HELVETICA = '"Helvetica Neue", Helvetica, Roboto, Arial, sans-serif !default;'
ARIAL = 'Arial, sans-serif !default;'
VERDANA = 'Verdana, Geneva, sans-serif !default;'
COURIER_NEW = '"Courier New", Courier, monospace !default;'     # monospace

# options editable by the user
user_options = {
    'primary-color': '#006fba',
    'font-family-sans-serif': HELVETICA
}

default_font_families = {
    'Helvetica': HELVETICA,
    'Arial': ARIAL,
    'Verdana': VERDANA,
    'Courier New': COURIER_NEW,
}


class OrgTheme(BaseTheme):
    name = 'onegov.org.foundation'

    _force_compile = False

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
        imports = [
            'foundation-mods',
        ]
        for font_family in self.additional_font_families:
            imports.append(font_family)
        return imports

    @property
    def post_imports(self):
        return [
            'org'
        ]

    @property
    def extra_search_paths(self):
        return [
            module_path('onegov.org.theme', 'styles'),
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
