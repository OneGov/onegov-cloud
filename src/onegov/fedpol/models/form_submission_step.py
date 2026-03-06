from __future__ import annotations

from onegov.form.parser import parse_form


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form import FormSubmission


class FormSubmissionStep:
    def __init__(self, submission: FormSubmission, step: int) -> None:
        self.submission = submission
        self.id = submission.id
        self.step = step

    @property
    def next_step(self) -> FormSubmissionStep | None:
        # FIXME: How do we handle form extensions better?
        form_class = parse_form(self.submission.definition)
        form = form_class(data=self.submission.data)
        for next_step in range(self.step + 1, 999):
            if next_step > len(form.fieldsets):
                return None

            # NOTE: If at least one of the fields in the next fieldset
            #       is visible, then that's our next step.
            fieldset = form.fieldsets[next_step - 1]
            if any(
                form.is_visible_through_dependencies(field_id)
                for field_id in fieldset.fields
            ):
                return FormSubmissionStep(self.submission, next_step)
        return None
