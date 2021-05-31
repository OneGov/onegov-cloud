from cached_property import cached_property

from onegov.file import File


class OpenGraphMixin:

    og_description_attr = 'lead'

    @property
    def og_title(self):
        return getattr(self, 'title', None) or \
            getattr(self.og_model, 'title', None)

    @property
    def og_type(self):
        return 'website'

    @property
    def og_url(self):
        return self.request.url

    @property
    def og_model(self):
        return self.model

    @property
    def og_site_name(self):
        """ Name of the overall Website """
        return self.org.name

    @cached_property
    def og_image_source(self):
        return self.org.og_logo_default

    @cached_property
    def og_image(self):
        """ File object to use for the site image. """
        url = self.og_image_source
        if not url or not self.is_internal(url):
            return
        fid = url.split('/')[-1]
        return self.request.session.query(File).filter_by(id=fid).first()

    @cached_property
    def og_image_url(self):
        return self.og_image and self.request.link(self.og_image)

    @property
    def og_description(self):
        return getattr(self.og_model, self.og_description_attr, None)

    @property
    def og_image_alt(self):
        if self.og_image:
            return self.og_image.reference.filename

    @property
    def og_image_type(self):
        if self.og_image:
            return self.og_image.reference.content_type

    @property
    def og_image_width(self):
        if self.og_image:
            size = getattr(self.og_image.reference, 'size', None)
            return size and size[0].replace('px', '') or None

    @property
    def og_image_height(self):
        if self.og_image:
            size = getattr(self.og_image.reference, 'size', None)
            return size and size[1].replace('px', '') or None

    @cached_property
    def og_locale(self):
        return self.request.locale

    @property
    def og_locale_alternate(self):
        return (
            la for la in self.request.app.settings.i18n.locales if
            not la == self.og_locale
        )

    def is_image_file(self, file):
        return hasattr(file.reference, 'size')

    def is_internal(self, path):
        return self.request.domain in path
