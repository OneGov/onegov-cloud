from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Public, Private
from onegov.org.forms.political_business import PoliticalBusinessForm
from onegov.org.collections.parliamentary_group import ParliamentaryGroupCollection
from onegov.org.collections.political_business_participant import (
    PoliticalBusinessParticipationCollection
)
from onegov.org.collections.political_business import PoliticalBusinessCollection
from onegov.org.models import PoliticalBusiness, ParliamentaryGroup
from onegov.org.models import PoliticalBusinessParticipation
from onegov.org.models.political_business import (
    POLITICAL_BUSINESS_STATUS)
from onegov.org.models.political_business import (
    POLITICAL_BUSINESS_TYPE)
from onegov.org.request import OrgRequest
from onegov.town6 import _
from onegov.town6 import TownApp
from onegov.town6.layout import PoliticalBusinessCollectionLayout
from onegov.town6.layout import PoliticalBusinessLayout

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from webob.response import Response

    from onegov.core.types import RenderData

    from onegov.town6.request import TownRequest


def get_political_business_form_class(
    model: object,
    request: OrgRequest
) -> type[PoliticalBusinessForm]:

    if isinstance(model, PoliticalBusiness):
        return model.with_content_extensions(PoliticalBusinessForm, request)
    return PoliticalBusiness(title='title').with_content_extensions(
        PoliticalBusinessForm, request
    )

@TownApp.html(
    model=PoliticalBusinessCollection,
    template='political_businesses.pt',
    permission=Public,
)
def view_political_businesses(
    self: PoliticalBusinessCollection,
    request: TownRequest,
    layout: PoliticalBusinessCollectionLayout | None = None
) -> RenderData | Response:

    return {
        # 'add_link': request.link(self, name='new'),
        'layout': layout or PoliticalBusinessCollectionLayout(self, request),
        'title': _('Political Businesses'),
        'businesses': self.batch,
        'type_map': POLITICAL_BUSINESS_TYPE,
        'status_map': POLITICAL_BUSINESS_STATUS,
    }


@TownApp.form(
    model=PoliticalBusinessCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=get_political_business_form_class
)
def view_add_political_business(
    self: PoliticalBusinessCollection,
    request: TownRequest,
    form: PoliticalBusinessForm,
) -> RenderData | Response:
    layout = PoliticalBusinessCollectionLayout(self, request)

    if form.submitted(request):
        data = form.get_useful_data()
        participations = data.pop('participations', [])
        political_business = self.add(**data)

        # extract participants
        collection = PoliticalBusinessParticipationCollection(request.session)
        participants = []

        for p in participations:
            id = p.get('person')
            role = p.get('role')
            if id and role:
                participant = collection.add(
                    political_business_id=political_business.id,
                    parliamentarian_id=id,
                    participant_type=role,
                )
                participants.append(participant)

        political_business.participants = participants
        request.success(_('Added a new political business'))

        return request.redirect(request.link(political_business))

    layout.breadcrumbs.append(Link(_('New'), '#'))

    return {
        'layout': layout,
        'title': _('New political business'),
        'form': form,
        'form_width': 'large',
    }


@TownApp.form(
    model=PoliticalBusiness,
    name='edit',
    template='form.pt',
    permission=Private,
    form=get_political_business_form_class
)
def edit_political_business(
    self: PoliticalBusiness,
    request: TownRequest,
    form: PoliticalBusinessForm,
) -> RenderData | Response:
    layout = PoliticalBusinessLayout(self, request)

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))

        return request.redirect(request.link(self))

    form.process(obj=self)

    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large',
    }


@TownApp.html(
    model=PoliticalBusiness,
    template='political_business.pt',
    permission=Public,
)
def view_political_business(
    self: PoliticalBusiness,
    request: TownRequest,
) -> RenderData | Response:
    layout = PoliticalBusinessLayout(self, request)

    political_groups = (
        ParliamentaryGroupCollection(request.session).query()
        .filter(ParliamentaryGroup.id == self.parliamentary_group_id)
        .order_by(ParliamentaryGroup.name)
        .all()
    )

    return {
        'layout': layout,
        'business': self,
        'title': self.title,
        'type_map': POLITICAL_BUSINESS_TYPE,
        'status_map': POLITICAL_BUSINESS_STATUS,
        'files': getattr(self, 'files', None),
        'political_groups': political_groups,
    }


@TownApp.view(
    model=PoliticalBusiness,
    request_method='DELETE',
    permission=Private,
)
def delete_political_business(
    self: PoliticalBusiness,
    request: TownRequest,
) -> None:

    request.assert_valid_csrf_token()

    # delete participations first
    participations = PoliticalBusinessParticipationCollection(request.session)
    participations.query().filter(
        PoliticalBusinessParticipation.political_business_id == self.id
    ).delete(synchronize_session=False)

    collection = PoliticalBusinessCollection(request.session)
    collection.delete(self)
