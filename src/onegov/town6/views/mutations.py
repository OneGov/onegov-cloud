from onegov.core.security import Private
from onegov.town6 import TownApp
from onegov.town6.layout import PageLayout
from onegov.org.forms.mutation import ApplyTopicMutationForm
from onegov.org.models.mutation import TopicMutation
from onegov.org.views.mutations import apply_topic_mutation


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=TopicMutation,
    name='apply',
    template='form.pt',
    permission=Private,
    form=ApplyTopicMutationForm
)
def apply_topic_mutation_town(
    self: TopicMutation,
    request: TownRequest,
    form: ApplyTopicMutationForm
) -> RenderData | Response:
    return apply_topic_mutation(
        self, request, form, PageLayout(self.target, request))
