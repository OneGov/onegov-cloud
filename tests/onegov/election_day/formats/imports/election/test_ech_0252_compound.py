from __future__ import annotations

from io import BytesIO
from onegov.election_day.formats import import_ech
from onegov.election_day.models import Canton
from xsdata_ech.e_ch_0155_5_0 import ElectionDescriptionInformationType
from xsdata_ech.e_ch_0155_5_0 import TypeOfElectionType
from xsdata_ech.e_ch_0252_2_0 import Delivery
from xsdata_ech.e_ch_0252_2_0 import DomainOfInfluenceType
from xsdata_ech.e_ch_0252_2_0 import DomainOfInfluenceTypeType
from xsdata_ech.e_ch_0252_2_0 import ElectionAssociationType
from xsdata_ech.e_ch_0252_2_0 import ElectionGroupInfoType
from xsdata_ech.e_ch_0252_2_0 import ElectionType
from xsdata_ech.e_ch_0252_2_0 import EventElectionInformationDeliveryType
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.models.datatype import XmlDate


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def create_delivery(
    compounds: list[str],
    elections: list[tuple[str, str | None]]
) -> Delivery:

    ElectionGroup = ElectionGroupInfoType.ElectionGroup
    ElectionDesc = ElectionDescriptionInformationType
    ElectionInfo = ElectionDesc.ElectionDescriptionInfo

    return Delivery(
        election_information_delivery=EventElectionInformationDeliveryType(
            polling_day=XmlDate(2023, 1, 1),
            election_association=[
                ElectionAssociationType(
                    election_association_id=identification,
                    election_association_name=identification
                ) for identification in compounds
            ],
            election_group_info=[
                ElectionGroupInfoType(
                    election_group=ElectionGroup(
                        domain_of_influence=DomainOfInfluenceType(
                            domain_of_influence_type=DomainOfInfluenceTypeType(
                                DomainOfInfluenceTypeType.MU
                            ),
                            domain_of_influence_identification='1701'
                        ),
                        election_information=[
                            ElectionGroup.ElectionInformation(
                                election=ElectionType(
                                    election_identification=id_,
                                    type_of_election=(
                                        TypeOfElectionType.VALUE_2
                                    ),
                                    number_of_mandates=1,
                                    election_description=ElectionDesc(
                                        election_description_info=[
                                            ElectionInfo(
                                                language='de',
                                                election_description=id_,
                                            )
                                        ]
                                    )
                                ),
                                referenced_election_association_id=association
                            )
                            for id_, association in elections
                        ]
                    )
                )
            ]
        )
    )


def test_import_ech_compound(session: Session) -> None:
    principal = Canton(canton='zg')
    serializer = XmlSerializer(config=SerializerConfig())

    # initial
    delivery = create_delivery(
        ['c-1', 'c-2', 'c-3'],
        [('e-1', 'c-1'), ('e-2', 'c-1'), ('e-3', 'c-2'), ('e-4', None)]
    )
    errors, updated_set, deleted = import_ech(
        principal,
        BytesIO(serializer.render(delivery).encode()),
        session,
        'de_CH'
    )
    session.flush()
    session.expire_all()
    assert not errors
    assert not deleted
    assert len(updated_set) == 7
    updated: dict[str, Any] = {item.id: item for item in updated_set}
    assert updated['c-1'].domain == 'canton'
    assert set(updated['c-1'].elections) == {updated['e-1'], updated['e-2']}
    assert updated['c-2'].domain == 'canton'
    assert updated['c-2'].elections == [updated['e-3']]
    assert updated['c-3'].domain == 'canton'
    assert updated['c-3'].elections == []
    assert updated['e-1'].domain == 'municipality'
    assert updated['e-2'].domain == 'municipality'
    assert updated['e-3'].domain == 'municipality'
    assert updated['e-3'].domain == 'municipality'

    # update
    delivery = create_delivery(
        ['c-1', 'c-3'],
        [('e-1', 'c-1'), ('e-2', 'c-3')]
    )
    errors, updated_set, deleted = import_ech(
        principal,
        BytesIO(serializer.render(delivery).encode()),
        session,
        'de_CH'
    )
    session.flush()
    session.expire_all()
    assert not errors
    assert len(deleted) == 3
    assert {item.id for item in deleted} == {'c-2', 'e-3', 'e-4'}
    assert len(updated_set) == 4
    updated = {item.id: item for item in updated_set}
    assert updated['c-1'].elections == [updated['e-1']]
    assert updated['c-3'].elections == [updated['e-2']]
