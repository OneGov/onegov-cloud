""" The settings view, defining things like the logo or color of the town. """

from onegov.core.security import Secret
from onegov.form import Form, with_options
from wtforms import StringField, TextAreaField, validators
from wtforms.widgets import TextArea
from wtforms_components import ColorField
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout
from onegov.town.model import Town


class SettingsForm(Form):
    """ Defines the settings form for onegov town. """

    name = StringField(_("Name"), [validators.InputRequired()])
    logo_url = StringField(
        label=_("Logo"),
        description=_("URL pointing to the logo")
    )
    primary_color = ColorField(_("Primary Color"))
    homepage_images = TextAreaField(
        label=_("Homepage Images"),
        description=_(
            "Up to six URLs pointing to images for the tiles on the homepage."
        ),
        widget=with_options(TextArea, rows=6)
    )

    @property
    def theme_options(self):
        options = {
            'primary-color': self.primary_color.data.get_hex(),
        }

        urls = (url.strip() for url in self.homepage_images.data.split('\n'))
        urls = (url for url in urls if url)

        for ix, url in enumerate(urls):
            # put the url in apostrophes, because it's a sass string
            options['tile-image-{}'.format(ix + 1)] = '"{}"'.format(url)

        return options

    @theme_options.setter
    def theme_options(self, theme_options):
        self.primary_color.data = theme_options.get('primary-color')

        tile_image_keys = ('tile-image-{}'.format(ix) for ix in range(1, 7))
        urls = (theme_options.get(key) for key in tile_image_keys)
        urls = (url.strip('"') for url in urls if url)

        self.homepage_images.data = '\n'.join(urls)


@TownApp.form(
    model=Town, name='einstellungen', template='form.pt', permission=Secret,
    form=SettingsForm)
def handle_settings(self, request, form):
    """ Handles the GET and POST login requests. """

    if form.submitted(request):
        with request.app.update_town() as town:
            town.name = form.name.data
            town.logo_url = form.logo_url.data
            town.theme_options = form.theme_options

        request.success(_(u"Your changes were saved."))
    else:
        form.name.data = self.name
        form.logo_url.data = self.logo_url
        form.theme_options = self.theme_options

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Settings"), request.link(self))
    ]

    return {
        'layout': layout,
        'title': _(u'Settings'),
        'form': form
    }
