from __future__ import annotations

from onegov.core.i18n import SiteLocale
from onegov.fedpol import FedpolApp
from onegov.fedpol.models import FormSubmissionStep
from onegov.form import FormCollection
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fedpol.request import FedpolRequest


@FedpolApp.path(
    model=SiteLocale,
    path='/locale/{locale}'
)
def get_locale(
    app: FedpolApp,
    locale: str
) -> SiteLocale | None:
    return SiteLocale.for_path(app, locale)


@FedpolApp.path(
    model=FormSubmissionStep,
    path='/form-preview-step/{id}/{step}',
    converters={'id': UUID, 'step': int}
)
def get_pending_form_submission(
    request: FedpolRequest,
    id: UUID,
    step: int
) -> FormSubmissionStep | None:
    if step < 1:
        return None
    submission = FormCollection(
        request.session
    ).submissions.by_id(id, state='pending', current_only=True)
    if submission is None:
        return None
    return FormSubmissionStep(submission, step)
