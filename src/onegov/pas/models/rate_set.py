from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from uuid import uuid4
from uuid import UUID


class RateSet(Base, ContentMixin, TimestampMixin):
    """ Sätze """

    __tablename__ = 'pas_rate_sets'

    #: Internal ID
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: The year
    year: Mapped[int]

    # FIXME: Is content_property appropriate for these? content is deferred
    #        so it will emit a second query the first time any one of these
    #        properties are accessed, are we only accessing these in a detail
    #        view and never in a listing? Then it might make sense.
    cost_of_living_adjustment: dict_property[float] = (
        content_property(default=0.0)
    )

    # The rates, naming schema is {attendence}_{commission}_{role}_{time}
    plenary_none_president_halfday: dict_property[int] = (
        content_property(default=0)
    )

    plenary_none_member_halfday: dict_property[int] = (
        content_property(default=0)
    )

    commission_normal_president_initial: dict_property[int] = (
        content_property(default=0)
    )

    commission_normal_president_additional: dict_property[int] = (
        content_property(default=0)
    )

    commission_normal_member_initial: dict_property[int] = (
        content_property(default=0)
    )

    commission_normal_member_additional: dict_property[int] = (
        content_property(default=0)

    )

    commission_intercantonal_president_halfday: dict_property[int] = (
        content_property(default=0)
    )

    commission_intercantonal_member_halfday: dict_property[int] = (
        content_property(default=0)

    )

    commission_official_president_halfday: dict_property[int] = (
        content_property(default=0)
    )

    commission_official_president_fullday: dict_property[int] = (
        content_property(default=0)

    )

    commission_official_vice_president_halfday: dict_property[int] = (
        content_property(default=0)
    )

    commission_official_vice_president_fullday: dict_property[int] = (
        content_property(default=0)

    )

    shortest_all_president_halfhour: dict_property[int] = (
        content_property(default=0)
    )

    shortest_all_member_halfhour: dict_property[int] = (
        content_property(default=0)

    )

    study_normal_president_halfhour: dict_property[int] = (
        content_property(default=0)
    )

    study_normal_member_halfhour: dict_property[int] = (
        content_property(default=0)
    )

    study_intercantonal_president_hour: dict_property[int] = (
        content_property(default=0)
    )

    study_intercantonal_member_hour: dict_property[int] = (
        content_property(default=0)
    )

    study_official_president_halfhour: dict_property[int] = (
        content_property(default=0)
    )

    study_official_member_halfhour: dict_property[int] = (
        content_property(default=0)
    )
