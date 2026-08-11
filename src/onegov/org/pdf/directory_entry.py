from __future__ import annotations

from html import escape
from io import BytesIO

from onegov.form.fields import UploadField, UploadMultipleField
from onegov.org import _
from onegov.org.layout import DefaultMailLayout
from onegov.org.pdf.core import OrgPdf
from onegov.pdf import page_fn_footer, page_fn_header_and_footer


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from markupsafe import Markup
    from onegov.org.models import ExtendedDirectoryEntry
    from onegov.org.request import OrgRequest
    from onegov.pdf.templates import Template
    from reportlab.pdfgen.canvas import Canvas


class DirectoryEntryPdf(OrgPdf):
    """ Certifies the publication of a directory entry, attached to the
    admin notifications sent when a publication starts or ends.

    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # our footer already prefixes a copyright, so skip OrgPdf's 'Source:'
        self.doc.author = kwargs.get('author', '')

    @property
    def page_fn(self) -> Callable[[Canvas, Template], None]:
        # the title is already part of the story, no header on the first page
        return page_fn_footer

    @property
    def page_fn_later(self) -> Callable[[Canvas, Template], None]:
        return page_fn_header_and_footer

    def add_title(
        self,
        entry: ExtendedDirectoryEntry,
        request: OrgRequest,
        ended: bool = False
    ) -> None:

        title = escape(entry.title)
        self.h(title)
        link = (
            f'<a href="{request.link(entry)}" color="{self.link_color}">'
            f'<u>{title}</u></a>'
        )
        if ended:
            intro = _(
                'The publication "${title}" has ended.',
                mapping={'title': link},
            )
        else:
            intro = _(
                'This document certifies the publication "${title}" as '
                'follows.',
                mapping={'title': link},
            )
        self.p_markup(intro)

    def add_fields(
        self,
        entry: ExtendedDirectoryEntry,
        layout: DefaultMailLayout
    ) -> None:

        self.h2(_('Publication'))

        form = entry.directory.form_class(data=entry.values)
        self.mini_html(Markup('<ul>{}</ul>'.format(Markup('').join(
            Markup('<li><strong>{}</strong>: {}').format(
                field.label.text,
                form.render_display(field)
            )
            for field in form
            if not isinstance(field, (UploadField, UploadMultipleField))
        ))

    def add_attachments(
        self,
        entry: ExtendedDirectoryEntry,
        layout: DefaultMailLayout
    ) -> None:

        self.h2(_('Attachments'))

        if not entry.files:
            self.mini_html(f'<p>{self.translate(_("None"))}</p>')
            return

        size_label = self.translate(_('Size'))
        date_label = self.translate(_('Date'))
        hash_label = self.translate(_('Hash'))
        bytes_label = self.translate(_('Bytes'))
        # bullet-less bold filename tight above its list, spaced between files
        name_style = self.style.normal.clone(
            'attachment_name', spaceBefore=12, spaceAfter=2
        )
        for file in entry.files:
            self.p_markup(f'<strong>{escape(file.name)}</strong>', name_style)
            self.mini_html(
                f'<ul>'
                f'<li>{size_label}: {file.reference.file.content_length} '
                f'{bytes_label}</li>'
                f'<li>{date_label}: '
                f'{layout.format_date(file.created, "datetime_long")}</li>'
                f'<li>{hash_label}: {file.checksum or file.id}</li>'
                f'</ul>'
            )

    def add_publication_details(
        self,
        entry: ExtendedDirectoryEntry,
        layout: DefaultMailLayout
    ) -> None:

        self.h2(_('Publication details'))

        not_set = self.translate(_('Not set'))
        start = (
            layout.format_date(entry.publication_start, 'datetime_long')
            if entry.publication_start else not_set
        )
        end = (
            layout.format_date(entry.publication_end, 'datetime_long')
            if entry.publication_end else not_set
        )
        details = '\n'.join([
            (
                f'<li><strong>{self.translate(_("Publication start:"))}'
                f'</strong> {start}</li>'
            ),
            (
                f'<li><strong>{self.translate(_("Publication end:"))}'
                f'</strong> {end}</li>'
            ),
            (
                f'<li><strong>{self.translate(_("Access"))}:</strong> '
                f'{layout.access_label(entry.access)}</li>'
            ),
            (
                f'<li><strong>{self.translate(_("Entry checksum"))}:</strong> '
                f'{entry.content_hash}</li>'
            ),
        ])
        self.mini_html(f'<ul>{details}</ul>')

    def add_generated_note(
        self,
        layout: DefaultMailLayout,
        generated_at: datetime
    ) -> None:

        text = _(
            'Email automatically generated by ${org} at ${timestamp}',
            mapping={
                'org': layout.org.title,
                'timestamp': layout.format_date(
                    generated_at, 'datetime_long'),
            },
        )
        self.p_markup(
            text, self.style.paragraph.clone('generated_footer',
                                             spaceBefore=20)
        )

    @classmethod
    def from_entry(
        cls,
        request: OrgRequest,
        entry: ExtendedDirectoryEntry,
        generated_at: datetime,
        ended: bool = False
    ) -> BytesIO:
        """ Creates a PDF representation of the published entry. """

        app = request.app
        layout = DefaultMailLayout(entry, request)

        result = BytesIO()
        pdf = cls(
            result,
            title=entry.title,
            author=app.org.title,
            locale=request.locale,
            translations=app.translations,
        )
        pdf.init_a4_portrait(
            page_fn=pdf.page_fn,
            page_fn_later=pdf.page_fn_later
        )
        pdf.add_title(entry, request, ended)
        pdf.add_fields(entry, layout)
        pdf.add_attachments(entry, layout)
        pdf.add_publication_details(entry, layout)
        pdf.add_generated_note(layout, generated_at)
        pdf.generate()

        result.seek(0)
        return result
