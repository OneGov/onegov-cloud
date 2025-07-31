from __future__ import annotations

from sqlalchemy import func

from onegov.core.elements import Link
from onegov.core.security import Public, Private
from onegov.org.forms.political_business import PoliticalBusinessForm
from onegov.org.models import PoliticalBusiness
from onegov.org.models import PoliticalBusinessCollection
from onegov.org.models import PoliticalBusinessParticipationCollection
from onegov.org.models import PoliticalBusinessParticipation
from onegov.org.models.political_business import POLITICAL_BUSINESS_STATUS
from onegov.org.models.political_business import POLITICAL_BUSINESS_TYPE
from onegov.town6 import _
from onegov.town6 import TownApp
from onegov.town6.layout import PoliticalBusinessCollectionLayout
from onegov.town6.layout import PoliticalBusinessLayout

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob.response import Response


def get_political_business_form_class(
    model: object,
    request: TownRequest
) -> type[PoliticalBusinessForm]:

    if isinstance(model, PoliticalBusiness):
        return model.with_content_extensions(PoliticalBusinessForm, request)
    return PoliticalBusiness(title='title').with_content_extensions(
        PoliticalBusinessForm, request
    )


def count_political_businesses_by_type(
    request: TownRequest
) -> dict[str, int]:
    session = request.session
    result = session.query(
        PoliticalBusiness.political_business_type,
        func.count(PoliticalBusiness.id).label('count')
    ).group_by(PoliticalBusiness.political_business_type).all()

    return dict(result)


def count_political_businesses_by_status(
    request: TownRequest
) -> dict[str, int]:
    session = request.session
    result = session.query(
        PoliticalBusiness.status,
        func.count(PoliticalBusiness.id).label('count')
    ).group_by(PoliticalBusiness.status).all()

    return dict(result)


def count_political_businesses_by_year(
    request: TownRequest
) -> dict[str, int]:
    session = request.session
    result = session.query(
        func.extract('year', PoliticalBusiness.entry_date).label('year'),
        func.count(PoliticalBusiness.id).label('count')
    ).group_by(func.extract('year', PoliticalBusiness.entry_date)).all()

    # convert decimal to string
    return {
        str(int(year)): count for year, count in result
    }


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

    count_per_business_type = count_political_businesses_by_type(request)
    types = sorted([
        Link(
            text=request.translate(text) +
                 f' ({count_per_business_type[type]})',
            active=type in self.types,
            url=request.link(self.for_filter(type=type)),
        )
        for type, text in POLITICAL_BUSINESS_TYPE.items()
        if (type in count_per_business_type and
            count_per_business_type[type] > 0)
    ], key=lambda x: x.text.lower() if x.text else '')

    count_per_status = count_political_businesses_by_status(request)
    status = sorted([
        Link(
            text=request.translate(text) +
                f' ({count_per_status[status]})',
            active=status in self.status,
            url=request.link(self.for_filter(status=status)),
        )
        for status, text in POLITICAL_BUSINESS_STATUS.items()
        if (status in count_per_status and count_per_status[status] > 0)
    ], key=lambda x: x.text.lower() if x.text else '')

    count_per_year = count_political_businesses_by_year(request)
    years = [
        Link(
            text=str(year_int) + f' ({count_per_year[str(year_int)]})',
            active=year_int in self.years,
            url=request.link(self.for_filter(year=year_int)),
        )
        for year_int in self.years_for_entries()
        if (str(year_int) in count_per_year and
            count_per_year[str(year_int)] > 0)
    ]

    return {
        # 'add_link': request.link(self, name='new'),
        'layout': layout or PoliticalBusinessCollectionLayout(self, request),
        'title': _('Political Businesses'),
        'businesses': self.batch,
        'type_map': POLITICAL_BUSINESS_TYPE,
        'status_map': POLITICAL_BUSINESS_STATUS,
        'business_types': types,
        'business_status': status,
        'years': years,
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
        political_business = self.add(**data)
        form.populate_obj(political_business)
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
    form=get_political_business_form_class,
    pass_model=True
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
    groups = [self.parliamentary_group] if self.parliamentary_group else []

    return {
        'layout': layout,
        'business': self,
        'title': self.title,
        'type_map': POLITICAL_BUSINESS_TYPE,
        'status_map': POLITICAL_BUSINESS_STATUS,
        'files': getattr(self, 'files', None),
        'political_groups': groups,
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
