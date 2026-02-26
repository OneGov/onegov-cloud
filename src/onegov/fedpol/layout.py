from __future__ import annotations

from functools import cached_property
from onegov.core.elements import Link
from onegov.fedpol import _
from onegov.form import FormCollection, FormDefinition, FormSubmission
from onegov.form.parser import parse_form
from onegov.org.models.ticket import FormSubmissionTicket
from onegov.stepsequence import step_sequences, Step
from onegov.town6.layout import DefaultLayout
from onegov.town6.layout import (
    TicketChatMessageLayout as TownTicketChatMessageLayout)


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
        end_name = TicketChatMessageLayout.__name__
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
            Step(_('Check'), cls_name, num_steps + 1, end_name, cls_name),
            Step(_('Confirmation'), cls_name, num_steps + 2, None, cls_name),
        ]


class TicketChatMessageLayout(TownTicketChatMessageLayout):

    @cached_property
    def form_step_names(self) -> list[str] | None:
        if self.request.is_manager:
            return None

        if not isinstance(self.model, FormSubmissionTicket):
            return None

        submission = self.model.handler.submission
        if submission is None:
            return None

        fieldsets = parse_form(submission.definition)().fieldsets
        if len(fieldsets) < 2:
            return None

        form = submission.form
        form_title = _('Form') if form is None else form.title
        return [fieldset.label or form_title for fieldset in fieldsets]

    @property
    def step_position(self) -> int:
        if not self.form_step_names:
            return 3
        return len(self.form_step_names) + 2

    def get_step_sequence(self, position: int | None = None) -> list[Step]:
        if not self.form_step_names:
            return super().get_step_sequence(position)

        cls_name = FormSubmissionStepLayout.__name__
        end_name = self.__class__.__name__
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
            Step(_('Check'), cls_name, num_steps + 1, end_name, cls_name),
            Step(_('Confirmation'), cls_name, num_steps + 2, None, cls_name),
        ]
