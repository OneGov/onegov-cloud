""" The settings view, defining things like the logo or color of the town. """

from onegov.core.security import Secret
from onegov.form import Form, with_options
from wtforms import HiddenField, StringField, TextAreaField, validators
from wtforms.widgets import TextArea
from wtforms_components import ColorField
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout
from onegov.town.models import Town
from onegov.town.theme import user_options
from onegov.town.utils import linkify


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
    contact = TextAreaField(
        label=_("Contact"),
        description=_("The address and phone number of the municipality"),
        widget=with_options(TextArea, rows=8)
    )
    opening_hours = TextAreaField(
        label=_("Opening Hours"),
        description=_("The opening hours of the municipality"),
        widget=with_options(TextArea, rows=8)
    )

    # the footer height is determined by javascript, see town.scss and
    # common.js for more information (search for footer)
    footer_height = HiddenField()

    @property
    def theme_options(self):
        options = {
            'primary-color': self.primary_color.data.get_hex(),
            'footer-height': self.footer_height.data
        }

        # override the options using the default vaules if no value was given
        for key in options:
            if not options[key]:
                options[key] = user_options[key]

        urls = (url.strip() for url in self.homepage_images.data.split('\n'))
        urls = (url for url in urls if url)

        for ix, url in enumerate(urls):
            # put the url in apostrophes, because it's a sass string
            options['tile-image-{}'.format(ix + 1)] = '"{}"'.format(url)

        return options

    @theme_options.setter
    def theme_options(self, theme_options):
        self.primary_color.data = theme_options.get('primary-color')
        self.footer_height.data = theme_options.get('footer-height')

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
            town.meta = {
                'contact': form.contact.data,
                'contact_html': linkify(
                    form.contact.data).replace('\n', '<br>'),
                'opening_hours': form.opening_hours.data,
                'opening_hours_html': linkify(
                    form.opening_hours.data).replace('\n', '<br>')
            }

        request.success(_(u"Your changes were saved"))
    else:
        form.name.data = self.name
        form.logo_url.data = self.logo_url
        form.theme_options = self.theme_options
        form.contact.data = self.meta.get('contact')
        form.opening_hours.data = self.meta.get('opening_hours')

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Settings"), request.link(self))
    ]

    return {
        'layout': layout,
        'title': _(u'Settings'),
        'form': form,
        'form_width': 'large'
    }
