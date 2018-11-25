from datetime import datetime
from io import BytesIO
from morepath import redirect
from morepath.request import Response
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.utils import normalize_for_url
from onegov.gazette import _
from onegov.gazette import GazetteApp
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.collections.notices import TRANSLATIONS
from onegov.gazette.forms import EmptyForm
from onegov.gazette.forms import NoticeForm
from onegov.gazette.layout import Layout
from onegov.gazette.models import GazetteNotice
from onegov.gazette.pdf import IndexPdf
from onegov.gazette.pdf import NoticesPdf
from onegov.gazette.views import get_user
from onegov.gazette.views import get_user_and_group
from xlsxwriter import Workbook


@GazetteApp.form(
    model=GazetteNoticeCollection,
    name='new-notice',
    template='form.pt',
    permission=Personal,
    form=NoticeForm
)
def create_notice(self, request, form):
    """ Create a new notice.

    If a valid UID of a notice is given (via 'source' query parameter), its
    values are pre-filled in the form.

    This view is mainly used by the editors.

    """

    layout = Layout(self, request)
    user = get_user(request)

    if form.submitted(request):
        notice = self.add(
            title=form.title.data,
            text=form.text.data,
            author_place=form.author_place.data,
            author_date=form.author_date_utc,
            author_name=form.author_name.data,
            organization_id=form.organization.data,
            category_id=form.category.data,
            print_only=form.print_only.data if form.print_only else False,
            at_cost=form.at_cost.data == 'yes',
            billing_address=form.billing_address.data,
            user=get_user(request),
            issues=form.issues.data
        )
        if form.phone_number.data:
            user.phone_number = form.phone_number.data
        return redirect(request.link(notice))

    if not form.errors:
        if self.source:
            source = self.query().filter(GazetteNotice.id == self.source)
            source = source.first()
            if source:
                form.apply_model(source)
                if form.print_only:
                    form.print_only.data = False

        form.phone_number.data = user.phone_number

    return {
        'layout': layout,
        'form': form,
        'title': _("New Official Notice"),
        'helptext': _(
            "The fields marked with an asterisk * are mandatory fields."
        ),
        'button_text': _("Save"),
        'cancel': layout.dashboard_or_notices_link,
        'current_issue': layout.current_issue
    }


@GazetteApp.html(
    model=GazetteNoticeCollection,
    template='notices.pt',
    permission=Personal
)
def view_notices(self, request):
    """ View the list of notices.

    This view is only visible by a publisher. This (in the state 'accepted')
    is the view used by the publisher.

    """

    self.on_request(request)

    layout = Layout(self, request)
    is_publisher = request.is_private(self)

    states = ['drafted', 'submitted', 'accepted', 'rejected']
    if layout.importation:
        states.append('imported')
    if layout.publishing:
        states.append('published')

    filters = (
        {
            'title': _(state),
            'link': request.link(self.for_state(state)),
            'class': 'active' if state == self.state else ''
        }
        for state in states
    )

    orderings = {
        'title': {
            'title': _("Title"),
            'href': request.link(self.for_order('title')),
            'sort': self.direction if self.order == 'title' else '',
        },
        'organization': {
            'title': _("Organization"),
            'href': request.link(self.for_order('organization')),
            'sort': self.direction if self.order == 'organization' else '',
        },
        'category': {
            'title': _("Category"),
            'href': request.link(self.for_order('category')),
            'sort': self.direction if self.order == 'category' else '',
        },
        'group': {
            'title': _("Group"),
            'href': request.link(self.for_order('group.name')),
            'sort': self.direction if self.order == 'group.name' else '',
        },
        'user': {
            'title': _("User"),
            'href': request.link(self.for_order('user.name')),
            'sort': self.direction if self.order == 'user.name' else '',
        },
        'first_issue': {
            'title': _("Issue(s)"),
            'href': request.link(self.for_order('first_issue')),
            'sort': self.direction if self.order == 'first_issue' else '',
        }
    }

    title = _("Official Notices")
    if not is_publisher:
        self.user_ids, self.group_ids = get_user_and_group(request)
        filters = None
        title = _("Published Official Notices")

    preview = None
    index = None
    if is_publisher:
        preview = request.link(self, name='preview-pdf')
    if is_publisher and self.state == 'published':
        index = request.link(self, name='index')

    clear = {}
    if self.term:
        clear['term'] = request.link(self.for_term(None))
    if self.from_date or self.to_date:
        clear['dates'] = request.link(self.for_dates(None, None))
    if self.organizations:
        clear['organization'] = request.link(self.for_organizations(None))
    if self.categories:
        clear['category'] = request.link(self.for_categories(None))

    return {
        'layout': layout,
        'collection': self,
        'is_publisher': is_publisher,
        'notices': self.batch,
        'title': title,
        'filters': filters,
        'orderings': orderings,
        'clear': clear,
        'new_notice': request.link(self, name='new-notice'),
        'preview': preview,
        'index': index
    }


@GazetteApp.html(
    model=GazetteNoticeCollection,
    template='statistics.pt',
    name='statistics',
    permission=Private
)
def view_notices_statistics(self, request):
    """ View the list of notices.

    This view is only visible by a publisher. This (in the state 'accepted')
    is the view used by the publisher.

    """

    layout = Layout(self, request)

    states = ['drafted', 'submitted', 'accepted', 'rejected']
    if layout.importation:
        states.append('imported')
    if layout.publishing:
        states.append('published')

    filters = (
        {
            'title': _(state),
            'link': request.link(self.for_state(state), name='statistics'),
            'class': 'active' if state == self.state else ''
        }
        for state in states
    )

    return {
        'layout': layout,
        'filters': filters,
        'collection': self,
        'title': _("Statistics"),
        'from_date': self.from_date,
        'to_date': self.to_date,
        'by_organizations': self.count_by_organization(),
        'by_category': self.count_by_category(),
        'by_groups': self.count_by_group(),
        'rejected': self.count_rejected(),
        'clear': request.link(self.for_dates(None, None), name='statistics')
    }


@GazetteApp.view(
    model=GazetteNoticeCollection,
    name='statistics-xlsx',
    permission=Private
)
def view_notices_statistics_xlsx(self, request):
    """ View the statistics as XLSX. """

    output = BytesIO()
    workbook = Workbook(output)
    for title, row, content in (
        (_("Organizations"), _("Organization"), self.count_by_organization),
        (_("Categories"), _("Category"), self.count_by_category),
        (_("Groups"), _("Group"), self.count_by_group),
        (_("Rejected"), _("Name"), self.count_rejected),
    ):
        worksheet = workbook.add_worksheet()
        worksheet.name = request.translate(title)
        worksheet.write_row(0, 0, (
            request.translate(row),
            request.translate(_("Count"))
        ))
        for index, row in enumerate(content()):
            worksheet.write_row(index + 1, 0, row)
    workbook.close()
    output.seek(0)

    response = Response()
    response.content_type = (
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response.content_disposition = 'inline; filename={}-{}-{}.xlsx'.format(
        request.translate(_("Statistics")).lower(),
        normalize_for_url(request.translate(TRANSLATIONS.get(self.state, ''))),
        datetime.utcnow().strftime('%Y%m%d%H%M')
    )
    response.body = output.read()

    return response


@GazetteApp.view(
    model=GazetteNoticeCollection,
    name='preview-pdf',
    permission=Private
)
def view_notices_preview_pdf(self, request):
    """ Preview the notices as PDF.

    This view is only visible by a publisher.

    """

    pdf = NoticesPdf.from_notices(self, request)

    filename = normalize_for_url(
        '{}-{}'.format(
            request.translate(_("Gazette")),
            request.app.principal.name
        )
    )

    return Response(
        pdf.read(),
        content_type='application/pdf',
        content_disposition=f'inline; filename={filename}.pdf'
    )


@GazetteApp.view(
    model=GazetteNoticeCollection,
    name='index',
    permission=Private
)
def view_notices_index(self, request):
    """ Export the index to the notices as PDF.

    This view is only visible by a publisher.

    """

    pdf = IndexPdf.from_notices(self, request)

    filename = normalize_for_url(
        '{}-{}'.format(
            request.translate(_("Gazette")),
            request.app.principal.name
        )
    )

    return Response(
        pdf.read(),
        content_type='application/pdf',
        content_disposition=f'inline; filename={filename}.pdf'
    )


@GazetteApp.form(
    model=GazetteNoticeCollection,
    name='update',
    template='form.pt',
    permission=Private,
    form=EmptyForm
)
def view_notices_update(self, request, form):
    """ Updates all notices (of this state): Applies the categories, issues and
    organization from the meta informations. This view is not used normally
    and only intended when changing category names in the principal definition,
    for example.

    """

    layout = Layout(self, request)
    session = request.session

    if form.submitted(request):
        for notice in self.query():
            notice.apply_meta(session)
        request.message(_("Notices updated."), 'success')

        return redirect(layout.dashboard_or_notices_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("Update notices"),
        'button_text': _("Update"),
        'cancel': layout.dashboard_or_notices_link
    }
