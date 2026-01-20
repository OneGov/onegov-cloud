from __future__ import annotations

from collections import OrderedDict
from onegov.core.security import Public
from onegov.file import File
from onegov.file.utils import name_without_extension
from onegov.org import OrgApp, _
from onegov.org.layout import PublicationLayout
from onegov.org.models import GeneralFileCollection
from onegov.org.models import PublicationCollection
from onegov.core.elements import Link
from sqlalchemy import desc, literal


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime
    from onegov.core.types import RenderData
    from onegov.file.types import FileStats
    from onegov.org.request import OrgRequest
    from typing import NamedTuple

    class FileRow(NamedTuple):
        id: str
        name: str
        stats: FileStats | None
        created: datetime


MONTHS = (
    _('January'),
    _('Feburary'),
    _('March'),
    _('April'),
    _('May'),
    _('June'),
    _('July'),
    _('August'),
    _('September'),
    _('October'),
    _('November'),
    _('December'),
)


@OrgApp.html(
    model=PublicationCollection,
    permission=Public,
    template='publications.pt'
)
def view_publications(
    self: PublicationCollection,
    request: OrgRequest,
    layout: PublicationLayout | None = None
) -> RenderData:

    layout = layout or PublicationLayout(self, request)

    # filter by year, from latest to first year
    s = self.first_year(layout.timezone) or self.year
    e = layout.today().year
    years = range(e, s - 1, -1) if s is not None else ()

    filters = {
        'years': tuple(
            Link(
                text=str(year),
                active=year == self.year,
                url=request.link(self.for_year(year=year)),
                rounded=True
            ) for year in years
        )
    }

    # load the publications and bucket them into months
    publications: Sequence[list[FileRow]] = tuple([] for i in range(12))

    query = self.query().with_entities(
        File.id,
        File.name,
        File.stats,
        File.created.op('AT TIME ZONE')(
            literal(layout.timezone.zone)
        ).label('created'),
    ).order_by(desc(File.created))

    for f in query:
        publications[f.created.month - 1].append(f)

    # group the publications by months, while merging empty months
    today = layout.today()
    grouped: dict[str, list[FileRow] | None] = OrderedDict()
    spool: Sequence[str] = ()

    def apply_spool(spool: Sequence[str]) -> Sequence[str]:
        if spool:
            if len(spool) == 1:
                label = spool[0]
            else:
                label = f'{spool[0]} - {spool[-1]}'

            grouped[label] = None

        return ()

    for ix, publications_ in enumerate(reversed(publications)):
        month = 12 - ix

        # exclude current year's months if they are in the future
        if self.year == today.year and month > today.month:
            continue

        if not publications_:
            spool = (*spool, request.translate(MONTHS[month - 1]))
            continue

        spool = apply_spool(spool)
        grouped[request.translate(MONTHS[month - 1])] = publications_

    apply_spool(spool)

    # link to file and thumbnail by id
    def link(f: FileRow, name: str = '') -> str:
        return request.class_link(File, {'id': f.id}, name=name)

    return {
        'title': _('Publications'),
        'layout': layout,
        'model': self,
        'filters': filters,
        'link': link,
        'grouped': grouped,
        'name_without_extension': name_without_extension,
        'filedigest_handler': request.class_link(
            GeneralFileCollection, name='digest'
        )
    }
