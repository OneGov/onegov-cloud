from __future__ import annotations

from functools import cached_property

from onegov.file import File


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.org.models import Organisation
    from onegov.org.request import OrgRequest


class OpenGraphMixin:

    if TYPE_CHECKING:
        model: Any
        request: OrgRequest

        @property
        def org(self) -> Organisation: ...

    og_description_attr = 'lead'

    @property
    def og_title(self) -> str | None:
        return (
            getattr(self, 'title', None)
            or getattr(self.og_model, 'title', None)
        )

    @property
    def og_type(self) -> str:
        return 'website'

    @property
    def og_url(self) -> str:
        return self.request.url

    @property
    def og_model(self) -> Any:
        return self.model

    @property
    def og_site_name(self) -> str:
        """ Name of the overall Website """
        return self.org.name

    @cached_property
    def og_image_source(self) -> str | None:
        return self.org.og_logo_default

    @cached_property
    def og_image(self) -> File | None:
        """ File object to use for the site image. """
        url = self.og_image_source
        if not url or not self.is_internal(url):
            return None
        fid = url.split('/')[-1]
        return self.request.session.query(File).filter_by(id=fid).first()

    @cached_property
    def og_image_url(self) -> str | None:
        if self.og_image:
            return self.request.link(self.og_image)
        return None

    @property
    def og_description(self) -> str | None:
        return getattr(self.og_model, self.og_description_attr, None)

    @property
    def og_image_alt(self) -> str | None:
        if self.og_image:
            return self.og_image.reference.filename
        return None

    @property
    def og_image_type(self) -> str | None:
        if self.og_image:
            return self.og_image.reference.content_type
        return None

    @property
    def og_image_width(self) -> str | None:
        if self.og_image:
            size = getattr(self.og_image.reference, 'size', None)
            return size and size[0].replace('px', '') or None
        return None

    @property
    def og_image_height(self) -> str | None:
        if self.og_image:
            size = getattr(self.og_image.reference, 'size', None)
            return size and size[1].replace('px', '') or None
        return None

    @cached_property
    def og_locale(self) -> str | None:
        return self.request.locale

    @property
    def og_locale_alternate(self) -> Iterator[str]:
        return (
            locale
            for locale in self.request.app.settings.i18n.locales
            if locale != self.og_locale
        )

    def is_image_file(self, file: File) -> bool:
        return hasattr(file.reference, 'size')

    def is_internal(self, path: str) -> bool:
        return self.request.domain in path
