from decimal import Decimal
from xsdata_ech.e_ch_0252_1_0 import CountingCircleInfoType
from xsdata_ech.e_ch_0252_1_0 import CountingCircleType
from xsdata_ech.e_ch_0252_1_0 import CountOfVotersInformationType
from xsdata_ech.e_ch_0252_1_0 import DecisiveMajorityType
from xsdata_ech.e_ch_0252_1_0 import Delivery
from xsdata_ech.e_ch_0252_1_0 import DomainOfInfluenceType
from xsdata_ech.e_ch_0252_1_0 import EventVoteBaseDeliveryType
from xsdata_ech.e_ch_0252_1_0 import NamedIdType
from xsdata_ech.e_ch_0252_1_0 import ResultDataType
from xsdata_ech.e_ch_0252_1_0 import VoteInfoType
from xsdata_ech.e_ch_0252_1_0 import VoterTypeType
from xsdata_ech.e_ch_0252_1_0 import VoteSubTypeType
from xsdata_ech.e_ch_0252_1_0 import VoteTitleInformationType
from xsdata_ech.e_ch_0252_1_0 import VoteType
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.models.datatype import XmlDate


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ballot.models import Ballot
    from onegov.ballot.models import Vote


def export_ballot_ech_0252(
    ballot: 'Ballot',
    canton_id: int,
    domain_of_influence: DomainOfInfluenceType
) -> VoteInfoType:
    """ Returns all data as an eCH-0252 VoteInfoType. """

    SubtotalInfo = CountOfVotersInformationType.SubtotalInfo
    polling_day = XmlDate.from_date(ballot.vote.date)
    main_vote_identification = ballot.vote.external_id or ballot.vote.id
    if ballot.type == 'proposal':
        identification = main_vote_identification
    else:
        identification = (
            ballot.external_id or f'{main_vote_identification}-{ballot.type}'
        )

    translations = ballot.title_translations or ballot.vote.title_translations
    vote_sub_type = {
        'proposal': VoteSubTypeType.VALUE_1,
        'counter-proposal': VoteSubTypeType.VALUE_2,
        'tie-breaker': VoteSubTypeType.VALUE_3
    }.get(ballot.type)

    vote = VoteType(
        vote_identification=identification,
        main_vote_identification=main_vote_identification,
        other_identification=[
            NamedIdType(
                id_name='onegov',
                id=str(ballot.id)
            )
        ],
        domain_of_influence=domain_of_influence,
        polling_day=polling_day,
        vote_title_information=[
            VoteTitleInformationType(
                language=locale,
                vote_title=title,
            )
            for locale, title in translations.items() if title
        ],
        decisive_majority=DecisiveMajorityType.VALUE_1,
        vote_sub_type=vote_sub_type
    )
    counting_circle_info = [
        CountingCircleInfoType(
            counting_circle=CountingCircleType(
                counting_circle_id=(
                    str(result.entity_id) if result.entity_id
                    else f'19{canton_id:02d}0'
                ),
                counting_circle_name=result.name,
            ),
            result_data=ResultDataType(
                count_of_voters_information=CountOfVotersInformationType(
                    count_of_voters_total=result.eligible_voters,
                    subtotal_info=[
                        SubtotalInfo(
                            count_of_voters=result.expats,
                            voter_type=VoterTypeType.VALUE_2,
                        )
                    ] if result.expats else []
                ),
                fully_counted_true=result.counted,
                voter_turnout=Decimal(format(result.turnout, '5.2f')),
                received_invalid_votes=result.invalid,
                received_blank_votes=result.empty,
                count_of_yes_votes=result.yeas,
                count_of_no_votes=result.nays,
            )
        )
        for result in ballot.results
    ]
    return VoteInfoType(
        vote=vote,
        counting_circle_info=counting_circle_info
    )


def export_vote_ech_0252(
    vote: 'Vote',
    canton_id: int,
    domain_of_influence: DomainOfInfluenceType
) -> str:
    """ Returns all data as an eCH-0252 XML. """

    polling_day = XmlDate.from_date(vote.date)
    ballots = vote.ballots.all()
    delivery = Delivery(
        vote_base_delivery=EventVoteBaseDeliveryType(
            canton_id=canton_id,
            polling_day=polling_day,
            vote_info=[
                export_ballot_ech_0252(ballot, canton_id, domain_of_influence)
                for ballot in ballots
            ],
            number_of_entries=len(ballots)
        )
    )
    config = SerializerConfig(pretty_print=True)
    serializer = XmlSerializer(config=config)
    return serializer.render(delivery)
