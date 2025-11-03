from __future__ import annotations

from onegov.activity import ActivityFilter
from onegov.feriennet import FeriennetApp, _


from typing import TYPE_CHECKING

from onegov.feriennet.collections import MatchCollection
from onegov.feriennet.collections.activity import VacationActivityCollection
from onegov.feriennet.models.activity import VacationActivity
from onegov.feriennet.utils import (activity_ages, activity_min_cost,
                                    activity_spots)
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.feriennet.layout import DefaultLayout


@FeriennetApp.homepage_widget(tag='registration')
class RegistrationWidget:
    template = """
        <xsl:template match="registration">
            <div tal:condition="not:request.is_logged_in" class="register">
                <a href="./auth/register" class="button">
                    ${register_text}
                </a>
                <a href="./auth/login" class="button secondary">
                    ${login_text}
                </a>
            </div>
            <div tal:condition="request.is_logged_in" class="register">
                <a href="./userprofile" class="button secondary">
                    ${profile_text}
                </a>
            </div>
        </xsl:template>
    """

    def get_variables(self, layout: DefaultLayout) -> RenderData:
        return {
            'register_text': _('Register a new account'),
            'login_text': _('Go to Login'),
            'profile_text': _('Go to Profile')
        }


@FeriennetApp.homepage_widget(tag='activities')
class ActivitiesWidget:
    template = """
        <xsl:template match="activities">
            <tal:b metal:use-macro="layout.macros['activities_homepage']" />
        </xsl:template>
    """

    def get_variables(self, layout: DefaultLayout) -> RenderData:

        if layout.app.active_period:
            occasions = list(MatchCollection(
                layout.app.session(),
                layout.app.active_period,
                ['unoperable', 'empty', 'operable']).occasions)

            state_order = {'unoperable': 0, 'empty': 1, 'operable': 2}
            occasions = sorted(
                occasions,
                key=lambda o: state_order[o.state]  # type: ignore
            )

            activity_ids = (o.activity_id for o in occasions)
            unique_activity_ids = list(set(activity_ids))[:6]
            activities = VacationActivityCollection(layout.app.session()
                                                    ).query(
            ).filter(VacationActivity.id.in_(unique_activity_ids)).all()

            if len(activities) < 6:
                filter_obj = ActivityFilter()
                filter_obj.period_ids = (
                {layout.app.active_period.id
                 } if layout.app.active_period else set())
                rest_activities = VacationActivityCollection(
                    layout.app.session(),
                    filter=filter_obj,
                    ).query().filter(
                    VacationActivity.id.notin_(unique_activity_ids)).limit(
                        6 - len(activities))
                activities = activities + rest_activities.all()
        else:
            activities = []

        return {
            'activities': activities,
            'activities_link': layout.request.class_link(
                VacationActivityCollection),
            'activity_ages': activity_ages,
            'activity_min_cost': activity_min_cost,
            'activity_spots': activity_spots
        }
