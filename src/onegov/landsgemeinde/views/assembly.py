from __future__ import annotations

from morepath import redirect
from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.templates import render_macro
from onegov.landsgemeinde import _
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.collections import AgendaItemCollection
from onegov.landsgemeinde.collections import AssemblyCollection
from onegov.landsgemeinde.forms import AssemblyForm
from onegov.landsgemeinde.layouts import AssemblyCollectionLayout
from onegov.landsgemeinde.layouts import AssemblyLayout
from onegov.landsgemeinde.layouts import AssemblyTickerLayout
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models.assembly import STATES
from onegov.landsgemeinde.utils import ensure_states
from onegov.landsgemeinde.utils import update_ticker


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date, datetime
    from onegov.core.types import RenderData
    from onegov.file import File
    from onegov.landsgemeinde.request import LandsgemeindeRequest
    from webob import Response


def get_assembly_form_class(
    model: object,
    request: LandsgemeindeRequest
) -> type[AssemblyForm]:

    if isinstance(model, Assembly):
        return model.with_content_extensions(AssemblyForm, request)
    return Assembly().with_content_extensions(AssemblyForm, request)


@LandsgemeindeApp.html(
    model=AssemblyCollection,
    template='assemblies.pt',
    permission=Public
)
def view_assemblies(
    self: AssemblyCollection,
    request: LandsgemeindeRequest
) -> RenderData:

    layout = AssemblyCollectionLayout(self, request)

    return {
        'add_link': request.link(self, name='new'),
        'layout': layout,
        'assemblies': self.query().all(),
        'title': layout.title,
    }


@LandsgemeindeApp.form(
    model=AssemblyCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=get_assembly_form_class
)
def add_assembly(
    self: AssemblyCollection,
    request: LandsgemeindeRequest,
    form: AssemblyForm
) -> RenderData | Response:

    layout = AssemblyCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.include_editor()
    layout.edit_mode = True

    if form.submitted(request):
        assembly = self.add(
            date=form.date.data,
            state=form.state.data,
        )
        form.populate_obj(assembly)
        request.success(_('Added a new ${assembly}',
                          mapping={'assembly': layout.assembly_type}))

        return redirect(request.link(assembly))

    return {
        'layout': layout,
        'title': _('New ${assembly}',
                   mapping={'assembly': layout.assembly_type}),
        'form': form,
    }


@LandsgemeindeApp.html(
    model=Assembly,
    template='assembly.pt',
    permission=Public
)
def view_assembly(
    self: Assembly,
    request: LandsgemeindeRequest
) -> RenderData | Response:

    layout = AssemblyLayout(self, request)

    if not request.is_manager and layout.current_assembly() == self:
        return redirect(request.link(self, name='ticker'))

    return {
        'layout': layout,
        'assembly': self,
        'agenda_items': self.agenda_items,
        'title': layout.title,
    }


@LandsgemeindeApp.html(
    model=Assembly,
    name='ticker',
    template='ticker.pt',
    permission=Public
)
def view_assembly_ticker(
    self: Assembly,
    request: LandsgemeindeRequest
) -> RenderData:

    layout = AssemblyTickerLayout(self, request)

    agenda_items = (
        AgendaItemCollection(request.session)
        .preloaded_by_assembly(self).all()
    )

    return {
        'layout': layout,
        'assembly': self,
        'agenda_items': agenda_items,
        'title': layout.title,
    }


@LandsgemeindeApp.view(
    model=Assembly,
    name='ticker',
    request_method='HEAD',
    permission=Public
)
def view_assembly_ticker_head(
    self: Assembly,
    request: LandsgemeindeRequest
) -> None:

    @request.after
    def add_headers(response: Response) -> None:
        last_modified = self.last_modified or self.modified or self.created
        if last_modified:
            response.headers.add(
                'Last-Modified',
                last_modified.strftime('%a, %d %b %Y %H:%M:%S GMT')
            )


@LandsgemeindeApp.html(
    model=Assembly,
    name='states',
    template='states.pt',
    permission=Private
)
def view_assembly_states(
    self: Assembly,
    request: LandsgemeindeRequest
) -> RenderData:

    layout = AssemblyLayout(self, request)
    layout.editbar_links = []
    layout.breadcrumbs.append(Link(_('States'), '#'))

    agenda_items = (
        AgendaItemCollection(request.session)
        .preloaded_by_assembly(self).all()
    )

    return {
        'layout': layout,
        'assembly': self,
        'agenda_items': agenda_items,
        'title': layout.title,
    }


@LandsgemeindeApp.form(
    model=Assembly,
    name='edit',
    template='form.pt',
    permission=Private,
    form=AssemblyForm,
    pass_model=True
)
def edit_assembly(
    self: Assembly,
    request: LandsgemeindeRequest,
    form: AssemblyForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        updated = ensure_states(self)
        updated.add(self)
        update_ticker(request, updated)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    layout = AssemblyLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@LandsgemeindeApp.view(
    model=Assembly,
    request_method='DELETE',
    permission=Private
)
def delete_assembly(self: Assembly, request: LandsgemeindeRequest) -> None:

    request.assert_valid_csrf_token()

    collection = AssemblyCollection(request.session)
    collection.delete(self)


@LandsgemeindeApp.html(
    model=Assembly,
    template='open_data_info.pt',
    name='open-data',
    permission=Public
)
def view_assembly_open_data(
    self: Assembly,
    request: LandsgemeindeRequest
) -> RenderData | Response:

    layout = AssemblyLayout(self, request)

    if not request.is_manager and layout.current_assembly() == self:
        return redirect(request.link(self, name='ticker'))

    layout.breadcrumbs.append(Link(_('Open Data'), '#'))

    return {
        'layout': layout,
        'assembly': self,
        'agenda_items': self.agenda_items,
        'title': _('Open Data'),
    }


@LandsgemeindeApp.json(
    model=Assembly,
    name='json',
    permission=Public
)
def view_assembly_json(
    self: Assembly,
    request: LandsgemeindeRequest
) -> RenderData:

    agenda_items = (
        AgendaItemCollection(request.session)
        .preloaded_by_assembly(self).all()
    )

    def text(text: str | None) -> str | None:
        return text.strip() if text else None

    def link(file: File | None) -> str | None:
        return request.link(file) if file else None

    def isoformat(date_: date | datetime | None) -> str | None:
        return date_.isoformat() if date_ else None

    return {
        'date': isoformat(self.date),
        'state': self.state,
        'last_modified': isoformat(self.last_modified),
        'extraordinary': self.extraordinary,
        'video_url': self.video_url,
        'overview': text(self.overview),
        'files': {
            'memorial_pdf': link(self.memorial_pdf),
            'memorial_2_pdf': link(self.memorial_2_pdf),
            'memorial_supplement_pdf': link(self.memorial_supplement_pdf),
            'protocol_pdf': link(self.protocol_pdf),
            'audio_mp3': link(self.audio_mp3),
            'audio_zip': link(self.audio_zip),
        },
        'agenda_items': [{
            'number': item.number,
            'state': item.state,
            'last_modified': isoformat(item.last_modified),
            'irrelevant': item.irrelevant,
            'tacitly_accepted': item.tacitly_accepted,
            'title': text(item.title),
            'memorial_page': item.memorial_page,
            'overview': text(item.overview),
            'text': text(item.text),
            'resolution': text(item.resolution),
            'resolution_tags': item.resolution_tags,
            'files': {
                'memorial_pdf': link(item.memorial_pdf),
            },
            'vota': [{
                'number': votum.number,
                'state': votum.state,
                'text': text(votum.text),
                'motion': text(votum.motion),
                'statement_of_reasons': text(votum.statement_of_reasons),
                'person': {
                    'name': text(votum.person_name),
                    'function': text(votum.person_function),
                    'place': text(votum.person_place),
                    'political_affiliation': text(
                        votum.person_political_affiliation
                    ),
                    'picture': text(votum.person_picture)
                }
            } for votum in item.vota]
        } for item in agenda_items]
    }


@LandsgemeindeApp.view(
    model=Assembly,
    name='change-state',
    request_method='POST',
    permission=Private
)
def change_assembly_state(
    self: Assembly,
    request: LandsgemeindeRequest
) -> str:
    layout = AssemblyCollectionLayout(self, request)
    request.assert_valid_csrf_token()

    i = list(STATES).index(self.state)
    self.state = list(STATES)[(i + 1) % len(STATES)]

    updated = ensure_states(self)
    updated.add(self)
    update_ticker(request, updated)

    agenda_items = (
        AgendaItemCollection(request.session)
        .preloaded_by_assembly(self).all()
    )

    return render_macro(
        layout.macros['states-list'],
        request,
        {'assembly': self,
         'agenda_items': agenda_items,
         'layout': layout,
         'state': self.state}
    )
