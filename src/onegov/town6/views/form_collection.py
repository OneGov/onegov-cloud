from __future__ import annotations

from onegov.core.security import Public, Private
from onegov.form import FormCollection
from onegov.form.collection import SurveyCollection
from onegov.org.views.form_collection import (view_form_collection,
                                              view_survey_collection)
from onegov.town6 import TownApp
from onegov.town6.layout import FormCollectionLayout, SurveyCollectionLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@TownApp.html(model=FormCollection, template='forms.pt', permission=Public)
def town_view_form_collection(
    self: FormCollection,
    request: TownRequest
) -> RenderData:
    return view_form_collection(
        self, request, FormCollectionLayout(self, request))


@TownApp.html(model=SurveyCollection, template='surveys.pt',
              permission=Private)
def town_view_survey_collection(
    self: SurveyCollection,
    request: TownRequest
) -> RenderData:
    return view_survey_collection(
        self, request, SurveyCollectionLayout(self, request))
