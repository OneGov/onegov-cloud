""" Lists the custom forms. """
from __future__ import annotations

import collections
from markupsafe import Markup
from onegov.core.security import Public, Private
from onegov.form import FormCollection, FormDefinition
from onegov.form.collection import SurveyCollection
from onegov.form.models.definition import SurveyDefinition
from onegov.org.models.document_form import FormDocument
from onegov.org import _, OrgApp
from onegov.org.layout import FormCollectionLayout, SurveyCollectionLayout
from onegov.org.models.external_link import (
    ExternalLinkCollection, ExternalLink)
from onegov.org.views.form_definition import get_hints
from onegov.org.utils import group_by_column


from typing import cast, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    from collections.abc import Callable
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from typing import TypeAlias

    SortKey: TypeAlias = Callable[
        [FormDefinition | ExternalLink | FormDocument],
        SupportsRichComparison
    ]


def combine_grouped(
    items: dict[str, list[FormDefinition]],
    external_links: dict[str, list[ExternalLink]],
    document_forms: dict[str, list[FormDocument]],
    sort: SortKey | None = None
) -> dict[str, list[FormDefinition | ExternalLink | FormDocument]]:

    # NOTE: This is not safe, we are destroying the original items
    #       being passed in, but this is more memory efficient, and
    #       we don't reuse the original dictionaries
    result = cast(
        'dict[str, list[FormDefinition | ExternalLink | FormDocument]]',
        items
    )
    for key, values in external_links.items():
        if key not in items:
            result[key] = values  # type:ignore[assignment]
        else:
            result[key].extend(values)
            if sort:
                result[key].sort(key=sort)

    for key, values in document_forms.items():  # type:ignore[assignment]
        if key not in items:
            result[key] = values  # type:ignore[assignment]
        else:
            result[key].extend(values)
            if sort:
                result[key].sort(key=sort)

    return collections.OrderedDict(sorted(result.items()))


@OrgApp.html(model=FormCollection, template='forms.pt', permission=Public)
def view_form_collection(
    self: FormCollection,
    request: OrgRequest,
    layout: FormCollectionLayout | None = None
) -> RenderData:

    forms = group_by_column(
        request=request,
        query=self.definitions.query(),
        group_column=FormDefinition.group,
        sort_column=FormDefinition.order
    )

    ext_forms = group_by_column(
        request,
        query=ExternalLinkCollection.for_model(
            request.session, FormCollection
        ).query(),
        group_column=ExternalLink.group,
        sort_column=ExternalLink.order
    )

    document_forms = group_by_column(
        request,
        query=self.session.query(FormDocument),
        group_column=FormDocument.group,
        sort_column=FormDocument.order
    )

    layout = layout or FormCollectionLayout(self, request)

    def link_func(model: FormDefinition | ExternalLink) -> str:
        if isinstance(model, ExternalLink):
            return model.url
        return request.link(model)

    def edit_link(model: FormDefinition | ExternalLink) -> str | None:
        if isinstance(model, ExternalLink) and request.is_manager:
            title = request.translate(_('Edit external form'))
            to = request.class_link(FormCollection)
            return request.link(
                model,
                query_params={'title': title, 'to': to},
                name='edit'
            )
        return None

    def lead_func(model: FormDefinition | ExternalLink) -> str:
        lead = model.meta.get('lead')
        if not lead:
            lead = ''
        return lead

    # FIXME: Should the hint function be able to deal with ExternalLink?
    def hint(model: FormDefinition) -> str:
        hints = dict(get_hints(layout, model.current_registration_window))
        if hints:
            if 'stop' in hints:
                hint = Markup(
                    '<div class="hint-stop">{}</div>'
                ).format(request.translate(hints['stop']))
            else:
                if 'date' in hints:
                    hint = Markup(
                        '<div class="hint-date">{}</div>'
                    ).format(request.translate(hints['date']))
                if 'count' in hints:
                    hint += Markup(
                        '<div class="hint-count">{}</div>'
                    ).format(request.translate(hints['count']))
        return hint

    return {
        'layout': layout,
        'title': _('Forms'),
        'forms': combine_grouped(forms, ext_forms, document_forms,
                                  sort=lambda x: x.order),
        'link_func': link_func,
        'edit_link': edit_link,
        'lead_func': lead_func,
        'hint': hint,
    }


@OrgApp.html(model=SurveyCollection, template='surveys.pt', permission=Private)
def view_survey_collection(
    self: SurveyCollection,
    request: OrgRequest,
    layout: SurveyCollectionLayout | None = None
) -> RenderData:

    surveys = group_by_column(
        request=request,
        query=self.definitions.query(),
        group_column=SurveyDefinition.group,
        sort_column=SurveyDefinition.order
    )

    layout = layout or SurveyCollectionLayout(self, request)

    def link_func(model: SurveyDefinition) -> str:
        return request.link(model)

    def lead_func(model: SurveyDefinition) -> str:
        lead = model.meta.get('lead')
        if not lead:
            lead = ''
        return lead

    return {
        'layout': layout,
        'title': _('Surveys'),
        'surveys': surveys,
    }
