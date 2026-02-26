from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.fedpol import _
from onegov.form import FormCollection, FormDefinition, FormSubmission
from onegov.form.parser import parse_form
from onegov.stepsequence import step_sequences, Step
from onegov.town6.layout import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fedpol.models import FormSubmissionStep
    from onegov.fedpol.request import FedpolRequest


@step_sequences.registered_step(
    1, _('Form'), cls_after='FormSubmissionLayout')
class FormSubmissionStepLayout(DefaultLayout):

    model: FormDefinition | FormSubmission | FormSubmissionStep

    def __init__(
        self,
        model: FormDefinition | FormSubmission | FormSubmissionStep,
        request: FedpolRequest,
        title: str | None = None,
        step_title: str | None = None,
    ) -> None:

        super().__init__(model, request)
        self.include_code_editor()
        self.title = title or self.form.title
        self.step_title = step_title

    @cached_property
    def form(self) -> FormDefinition:
        if isinstance(self.model, FormDefinition):
            return self.model
        elif isinstance(self.model, FormSubmission):
            return self.model.form  # type: ignore[return-value]
        else:
            return self.model.submission.form  # type:ignore[return-value]

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        breadcrumbs = [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Forms'), self.request.class_link(FormCollection))
        ]
        if self.step_title and self.form:
            breadcrumbs.extend((
                Link(self.title, self.request.link(self.form)),
                Link(self.step_title, self.request.link(self.model)),
            ))
        else:
            breadcrumbs.append(
                Link(self.title, self.request.link(self.model))
            )
        return breadcrumbs

    @cached_property
    def form_step_names(self) -> list[str]:
        if isinstance(self.model, (FormDefinition, FormSubmission)):
            definition = self.model.definition
        else:
            definition = self.model.submission.definition

        return [
            fieldset.label or self.form.title
            for fieldset in parse_form(definition)().fieldsets
        ]

    @property
    def step_position(self) -> int:
        if isinstance(self.model, FormDefinition):
            return 1
        elif isinstance(self.model, FormSubmission):
            return len(self.form_step_names) + 1
        else:
            return self.model.step

    def get_step_sequence(self, position: int | None = None) -> list[Step]:
        cls_name = self.__class__.__name__
        num_steps = len(self.form_step_names)
        return [
            *(
                Step(
                    step_name,
                    cls_name,
                    idx,
                    cls_name,
                    cls_name if idx > 1 else None
                )
                for idx, step_name in enumerate(self.form_step_names, start=1)
            ),
            Step(_('Check'), cls_name, num_steps + 1, cls_name, cls_name),
            Step(_('Confirmation'), cls_name, num_steps + 2, None, cls_name),
        ]
