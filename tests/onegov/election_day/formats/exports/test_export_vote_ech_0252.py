from datetime import date
from json import loads
from onegov.ballot import Ballot
from onegov.ballot import BallotResult
from onegov.ballot import ComplexVote
from onegov.election_day.formats import export_vote_ech_0252
from xsdata_ech.e_ch_0155_5_0 import DomainOfInfluenceType
from xsdata_ech.e_ch_0155_5_0 import DomainOfInfluenceTypeType
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import JsonSerializer


def test_vote_export_ech_0252(session):
    vote = ComplexVote(
        title="Abstimmung",
        shortcode="FOO",
        domain='federation',
        date=date(2015, 6, 14)
    )
    vote.title_translations['it_CH'] = 'Votazione'

    session.add(vote)
    session.flush()

    def export_xml():
        domain = DomainOfInfluenceType(
            domain_of_influence_type=DomainOfInfluenceTypeType.CH,
            domain_of_influence_identification='1',
            domain_of_influence_name='Bund'
        )
        xml = export_vote_ech_0252(vote, 1, domain)
        parser = XmlParser()
        serializer = JsonSerializer()
        return loads(serializer.render(parser.from_string(xml)))

    assert export_xml()['voteBaseDelivery'] == {
        'cantonId': 1,
        'pollingDay': '2015-06-14',
        'voteInfo': [],
        'numberOfEntries': 0,
        'extension': None
    }

    vote.ballots.append(Ballot(type='proposal'))
    vote.ballots.append(
        Ballot(
            type='counter-proposal',
            title_translations={
                'de_CH': 'Gegenvorschlag',
                'it_CH': 'Controprogetto'
            }
        )
    )
    vote.ballots.append(
        Ballot(
            type='tie-breaker',
            title_translations={
                'de_CH': 'Stichfrage',
                'it_CH': 'Spareggio'
            }
        )
    )

    vote.proposal.results.append(
        BallotResult(
            name='Foo Town',
            counted=True,
            yeas=90,
            nays=45,
            invalid=5,
            empty=10,
            eligible_voters=150,
            expats=30,
            entity_id=1,
        )
    )
    vote.proposal.results.append(
        BallotResult(
            name='Bar Town',
            counted=False,
            entity_id=2,
        )
    )
    vote.counter_proposal.results.append(
        BallotResult(
            name='Foo Town',
            counted=False,
            entity_id=1,
        )
    )

    session.flush()

    export = export_xml()['voteBaseDelivery']
    assert export['numberOfEntries'] == 3
    assert len(export['voteInfo']) == 3
    assert export['voteInfo'][0]
    export = {vote['vote']['voteSubType']: vote for vote in export['voteInfo']}
    assert export[1]['vote'] == {
        "decisiveMajority": 1,
        "domainOfInfluence": {
            "domainOfInfluenceIdentification": "1",
            "domainOfInfluenceName": "Bund",
            "domainOfInfluenceShortname": None,
            "domainOfInfluenceType": "CH",
        },
        "grouping": None,
        "mainVoteIdentification": "abstimmung",
        "otherIdentification": [
            {"idName": "onegov", "id": str(vote.proposal.id)}
        ],
        "pollingDay": "2015-06-14",
        "sequence": None,
        "superiorAuthority": None,
        "voteIdentification": "abstimmung",
        "voteSubType": 1,
        "voteTitleInformation": [
            {
                "language": "de_CH", "voteTitle": "Abstimmung",
                "voteTitleShort": None
            },
            {
                "language": "it_CH", "voteTitle": "Votazione",
                "voteTitleShort": None
            },
        ],
    }
    assert export[2]["vote"] == {
        "decisiveMajority": 1,
        "domainOfInfluence": {
            "domainOfInfluenceIdentification": "1",
            "domainOfInfluenceName": "Bund",
            "domainOfInfluenceShortname": None,
            "domainOfInfluenceType": "CH",
        },
        "grouping": None,
        "mainVoteIdentification": "abstimmung",
        "otherIdentification": [
            {"id": str(vote.counter_proposal.id), "idName": "onegov"}
        ],
        "pollingDay": "2015-06-14",
        "sequence": None,
        "superiorAuthority": None,
        "voteIdentification": "abstimmung-counter-proposal",
        "voteSubType": 2,
        "voteTitleInformation": [
            {
                "language": "de_CH", "voteTitle": "Gegenvorschlag",
                "voteTitleShort": None
            },
            {
                "language": "it_CH", "voteTitle": "Controprogetto",
                "voteTitleShort": None
            },
        ],
    }
    assert export[3]["vote"] == {
        "decisiveMajority": 1,
        "domainOfInfluence": {
            "domainOfInfluenceIdentification": "1",
            "domainOfInfluenceName": "Bund",
            "domainOfInfluenceShortname": None,
            "domainOfInfluenceType": "CH",
        },
        "grouping": None,
        "mainVoteIdentification": "abstimmung",
        "otherIdentification": [
            {"id": str(vote.tie_breaker.id), "idName": "onegov"}
        ],
        "pollingDay": "2015-06-14",
        "sequence": None,
        "superiorAuthority": None,
        "voteIdentification": "abstimmung-tie-breaker",
        "voteSubType": 3,
        "voteTitleInformation": [
            {
                "language": "de_CH", "voteTitle": "Stichfrage",
                "voteTitleShort": None
            },
            {
                "language": "it_CH", "voteTitle": "Spareggio",
                "voteTitleShort": None
            },
        ],
    }
    results = {
        result['countingCircle']['countingCircleId']: result
        for result in export[1]['countingCircleInfo']
    }
    assert results['1'] == {
        "countingCircle": {
            "countingCircleId": "1",
            "countingCircleName": "Foo Town",
            "domainOfInfluenceType": None,
        },
        "resultData": {
            "countOfNoVotes": 45,
            "countOfVotersInformation": {
                "countOfVotersTotal": 150,
                "subtotalInfo": [{
                    "countOfVoters": 30, "sex": None, "voterType": 2
                }],
            },
            "countOfVotesWithoutAnswer": None,
            "countOfYesVotes": 90,
            "fullyCountedTrue": True,
            "lockoutTimeStamp": None,
            "namedElement": [],
            "receivedBlankVotes": 10,
            "receivedInvalidVotes": 5,
            "receivedValidVotes": None,
            "receivedVotes": None,
            "releasedTimeStamp": None,
            "voterTurnout": "100.00",
            "votingCardInformationType": None,
        },
    }
    assert results['2'] == {
        "countingCircle": {
            "countingCircleId": "2",
            "countingCircleName": "Bar Town",
            "domainOfInfluenceType": None,
        },
        "resultData": {
            "countOfNoVotes": 0,
            "countOfVotersInformation": {
                "countOfVotersTotal": 0, "subtotalInfo": []
            },
            "countOfVotesWithoutAnswer": None,
            "countOfYesVotes": 0,
            "fullyCountedTrue": False,
            "lockoutTimeStamp": None,
            "namedElement": [],
            "receivedBlankVotes": 0,
            "receivedInvalidVotes": 0,
            "receivedValidVotes": None,
            "receivedVotes": None,
            "releasedTimeStamp": None,
            "voterTurnout": "0.00",
            "votingCardInformationType": None,
        },
    }
    assert export[2]['countingCircleInfo'][0] == {
        "countingCircle": {
            "countingCircleId": "1",
            "countingCircleName": "Foo Town",
            "domainOfInfluenceType": None,
        },
        "resultData": {
            "countOfNoVotes": 0,
            "countOfVotersInformation": {
                "countOfVotersTotal": 0, "subtotalInfo": []
            },
            "countOfVotesWithoutAnswer": None,
            "countOfYesVotes": 0,
            "fullyCountedTrue": False,
            "lockoutTimeStamp": None,
            "namedElement": [],
            "receivedBlankVotes": 0,
            "receivedInvalidVotes": 0,
            "receivedValidVotes": None,
            "receivedVotes": None,
            "releasedTimeStamp": None,
            "voterTurnout": "0.00",
            "votingCardInformationType": None,
        },
    }
    assert export[3]['countingCircleInfo'] == []
