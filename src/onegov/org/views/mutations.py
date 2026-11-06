from morepath import redirect
from onegov.core.security import Private
from onegov.org import _
from onegov.org import OrgApp
from onegov.org.forms.mutation import ApplyTopicMutationForm
from onegov.org.layout import PageLayout
from onegov.org.models.mutation import TopicMutation
from onegov.org.models.message import TopicMutationMessage
from onegov.org.elements import Link


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from webob import Response


@OrgApp.form(
    model=TopicMutation,
    name='apply',
    template='form.pt',
    permission=Private,
    form=ApplyTopicMutationForm
)
def apply_topic_mutation(
    self: TopicMutation,
    request: OrgRequest,
    form: ApplyTopicMutationForm,
    layout: PageLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        form.update_model()
        assert self.ticket is not None
        request.success(_('Proposed changes applied.'))
        TopicMutationMessage.create(self.ticket, request, 'applied')
        if 'return-to' in request.GET:
            return request.redirect(request.url)
        return redirect(request.link(self))
    else:
        form.apply_model()

    layout = layout or PageLayout(self.target, request)
    layout.breadcrumbs = list(layout.breadcrumbs)
    layout.breadcrumbs.append(Link(_('Apply proposed changes'), '#'))

    return {
        'layout': layout,
        'title': _('Apply proposed changes'),
        'form': form
    }
