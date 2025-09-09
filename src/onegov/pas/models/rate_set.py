from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Integer
from uuid import uuid4

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from onegov.core.orm.mixins import dict_property


class RateSet(Base, ContentMixin, TimestampMixin):
    """ Sätze """

    __tablename__ = 'pas_rate_sets'

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The year
    year: Column[int] = Column(
        Integer,
        nullable=False
    )

    cost_of_living_adjustment: dict_property[float]
    cost_of_living_adjustment = content_property(default=0.0)

    # The rates, naming schema is {attendence}_{commission}_{role}_{time}
    plenary_none_president_halfday: dict_property[int]
    plenary_none_president_halfday = content_property(default=0)

    plenary_none_member_halfday: dict_property[int]
    plenary_none_member_halfday = content_property(default=0)

    commission_normal_president_initial: dict_property[int]
    commission_normal_president_initial = content_property(default=0)

    commission_normal_president_additional: dict_property[int]
    commission_normal_president_additional = content_property(default=0)

    commission_normal_member_initial: dict_property[int]
    commission_normal_member_initial = content_property(default=0)

    commission_normal_member_additional: dict_property[int]
    commission_normal_member_additional = content_property(default=0)

    commission_intercantonal_president_halfday: dict_property[int]
    commission_intercantonal_president_halfday = content_property(default=0)

    commission_intercantonal_member_halfday: dict_property[int]
    commission_intercantonal_member_halfday = content_property(default=0)

    commission_official_president_halfday: dict_property[int]
    commission_official_president_halfday = content_property(default=0)

    commission_official_president_fullday: dict_property[int]
    commission_official_president_fullday = content_property(default=0)

    commission_official_vice_president_halfday: dict_property[int]
    commission_official_vice_president_halfday = content_property(default=0)

    commission_official_vice_president_fullday: dict_property[int]
    commission_official_vice_president_fullday = content_property(default=0)

    shortest_all_president_halfhour: dict_property[int]
    shortest_all_president_halfhour = content_property(default=0)

    shortest_all_member_halfhour: dict_property[int]
    shortest_all_member_halfhour = content_property(default=0)

    study_normal_president_halfhour: dict_property[int]
    study_normal_president_halfhour = content_property(default=0)

    study_normal_member_halfhour: dict_property[int]
    study_normal_member_halfhour = content_property(default=0)

    study_intercantonal_president_hour: dict_property[int]
    study_intercantonal_president_hour = content_property(default=0)

    study_intercantonal_member_hour: dict_property[int]
    study_intercantonal_member_hour = content_property(default=0)

    study_official_president_halfhour: dict_property[int]
    study_official_president_halfhour = content_property(default=0)

    study_official_member_halfhour: dict_property[int]
    study_official_member_halfhour = content_property(default=0)
