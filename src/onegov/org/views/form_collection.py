""" Lists the custom forms. """

import collections
from onegov.core.security import Public
from onegov.form import FormCollection, FormDefinition
from onegov.org import _, OrgApp
from onegov.org.layout import FormCollectionLayout
from onegov.org.models.external_link import ExternalLinkCollection, \
    ExternalLink
from onegov.org.views.form_definition import get_hints
from onegov.org.utils import group_by_column


def combine_grouped(items, external_links, sort=None):
    for key, values in external_links.items():
        if key not in items:
            items[key] = values
        else:
            if sort:
                items[key] = sorted(items[key] + values, key=sort)
            else:
                items[key] += values
    return collections.OrderedDict(sorted(items.items()))


@OrgApp.html(model=FormCollection, template='forms.pt', permission=Public)
def view_form_collection(self, request, layout=None):

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

    layout = layout or FormCollectionLayout(self, request)

    def link_func(model):
        if isinstance(model, ExternalLink):
            return model.url
        return request.link(model)

    def edit_link(model):
        if isinstance(model, ExternalLink) and request.is_manager:
            title = request.translate(_("Edit external form"))
            to = request.class_link(FormCollection)
            return request.link(
                model,
                query_params={'title': title, 'to': to},
                name='edit'
            )

    def external_link(model):
        if isinstance(model, ExternalLink):
            title = request.translate(_("Edit external form"))
            to = request.class_link(FormCollection)
            return request.link(
                model,
                query_params={'title': title, 'to': to},
                name='edit'
            )

    def lead_func(model):
        lead = model.meta.get('lead')
        if not lead:
            lead = ''
        lead = layout.linkify(lead)
        return lead

    def hint(model):
        hints = dict(get_hints(layout, model.current_registration_window))
        if hints:
            if 'stop' in hints:
                hint = (
                    f'<div class="hint-stop">'
                    f'{request.translate(hints["stop"])}'
                    f'</div>'
                )
            else:
                if 'date' in hints:
                    hint = (
                        f'<div class="hint-date">'
                        f'{request.translate(hints["date"])}'
                        f'</div>'
                    )
                if 'count' in hints:
                    hint += (
                        f'<div class="hint-count">'
                        f'{request.translate(hints["count"])}'
                        f'</div>'
                    )
        return hint

    return {
        'layout': layout,
        'title': _("Forms"),
        'forms': combine_grouped(forms, ext_forms, sort=lambda x: x.order),
        'link_func': link_func,
        'edit_link': edit_link,
        'external_link': external_link,
        'lead_func': lead_func,
        'hint': hint
    }
