from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.fedpol import _
from onegov.form import FormCollection, FormDefinition
from onegov.stepsequence import step_sequences
from onegov.town6.layout import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fedpol.models import FormSubmissionStep
    from onegov.fedpol.request import FedpolRequest


# FIXME: Dynamic steps
@step_sequences.registered_step(
    1, _('Form'), cls_after='FormSubmissionLayout')
class FormSubmissionStepLayout(DefaultLayout):

    model: FormSubmissionStep | FormDefinition

    def __init__(
        self,
        model: FormSubmissionStep | FormDefinition,
        request: FedpolRequest,
        title: str | None = None,
    ) -> None:

        super().__init__(model, request)
        self.include_code_editor()
        self.title = title or self.form.title

    @cached_property
    def form(self) -> FormDefinition:
        if hasattr(self.model, 'submission'):
            return self.model.submission.form  # type:ignore[return-value]
        else:
            return self.model

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Forms'), self.request.class_link(FormCollection)),
            Link(self.title, self.request.link(self.model))
        ]
