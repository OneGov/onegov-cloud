from collections import OrderedDict
from decimal import Decimal
from onegov.ballot.models.mixins import DomainOfInfluenceMixin
from onegov.ballot.models.mixins import ExplanationsPdfMixin
from onegov.ballot.models.mixins import LastModifiedMixin
from onegov.ballot.models.mixins import StatusMixin
from onegov.ballot.models.mixins import summarized_property
from onegov.ballot.models.mixins import TitleTranslationsMixin
from onegov.ballot.models.vote.ballot import Ballot
from onegov.ballot.models.vote.ballot_result import BallotResult
from onegov.ballot.models.vote.mixins import DerivedBallotsCountMixin
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.types import HSTORE
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy_utils import observes
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from uuid import uuid4
from xsdata_ech.e_ch_0252_1_0 import CountingCircleInfoType
from xsdata_ech.e_ch_0252_1_0 import CountingCircleType
from xsdata_ech.e_ch_0252_1_0 import CountOfVotersInformationType
from xsdata_ech.e_ch_0252_1_0 import DecisiveMajorityType
from xsdata_ech.e_ch_0252_1_0 import Delivery
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


SubtotalInfo = CountOfVotersInformationType.SubtotalInfo


class Vote(Base, ContentMixin, LastModifiedMixin,
           DomainOfInfluenceMixin, StatusMixin, TitleTranslationsMixin,
           DerivedBallotsCountMixin, ExplanationsPdfMixin):
    """ A vote describes the issue being voted on. For example,
    "Vote for Net Neutrality" or "Vote for Basic Income".

    """

    __tablename__ = 'votes'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'simple'
    }

    #: identifies the vote, may be used in the url, generated from the title
    id = Column(Text, primary_key=True)

    #: external identifier
    external_id = Column(Text, nullable=True)

    #: shortcode for cantons that use it
    shortcode = Column(Text, nullable=True)

    #: all translations of the title
    title_translations = Column(HSTORE, nullable=False)

    #: the translated title (uses the locale of the request, falls back to the
    #: default locale of the app)
    title = translation_hybrid(title_translations)

    @observes('title_translations')
    def title_observer(self, translations):
        if not self.id:
            self.id = self.id_from_title(object_session(self))

    #: identifies the date of the vote
    date = Column(Date, nullable=False)

    #: a vote contains n ballots
    ballots = relationship(
        'Ballot',
        cascade='all, delete-orphan',
        order_by='Ballot.type',
        backref=backref('vote'),
        lazy='dynamic'
    )

    def ballot(self, ballot_type, create=False):
        """ Returns the given ballot if it exists. Optionally creates the
        ballot.

        """

        result = [b for b in self.ballots if b.type == ballot_type]
        result = result[0] if result else None

        if not result and create:
            result = Ballot(id=uuid4(), type=ballot_type)
            self.ballots.append(result)

        return result

    @property
    def proposal(self):
        return self.ballot('proposal', create=True)

    @property
    def counted(self):
        """ Checks if there are results for all entitites. """

        if not self.ballots.first():
            return False

        for ballot in self.ballots:
            if not ballot.counted:
                return False

        return True

    @property
    def has_results(self):
        """ Returns True, if there are any results. """

        if not self.ballots.first():
            return False

        for ballot in self.ballots:
            for result in ballot.results:
                if result.counted:
                    return True

        return False

    @property
    def answer(self):
        if not self.counted or not self.proposal:
            return None

        return 'accepted' if self.proposal.accepted else 'rejected'

    @property
    def yeas_percentage(self):
        """ The percentage of yeas (discounts empty/invalid ballots). """

        return self.yeas / ((self.yeas + self.nays) or 1) * 100

    @property
    def nays_percentage(self):
        """ The percentage of nays (discounts empty/invalid ballots). """

        return 100 - self.yeas_percentage

    @property
    def progress(self):
        """ Returns a tuple with the first value being the number of counted
        entities and the second value being the number of total entities.

        We assume that for complex votes, every ballot has the same progress.
        """

        ballot_ids = set(b.id for b in self.ballots)

        if not ballot_ids:
            return 0, 0

        query = object_session(self).query(BallotResult)
        query = query.with_entities(BallotResult.counted)
        query = query.filter(BallotResult.ballot_id.in_(ballot_ids))

        results = query.all()
        divider = len(ballot_ids) or 1

        return (
            int(sum(1 for r in results if r[0]) / divider),
            int(len(results) / divider)
        )

    @property
    def counted_entities(self):
        """ Returns the names of the already counted entities. """

        ballot_ids = set(b.id for b in self.ballots)

        if not ballot_ids:
            return []

        query = object_session(self).query(BallotResult.name)
        query = query.filter(BallotResult.counted.is_(True))
        query = query.filter(BallotResult.ballot_id.in_(ballot_ids))
        query = query.order_by(BallotResult.name)
        query = query.distinct()
        return [result.name for result in query.all() if result.name]

    #: the total yeas
    yeas = summarized_property('yeas')

    #: the total nays
    nays = summarized_property('nays')

    #: the total empty votes
    empty = summarized_property('empty')

    #: the total invalid votes
    invalid = summarized_property('invalid')

    #: the total eligible voters
    eligible_voters = summarized_property('eligible_voters')

    #: the total expats
    expats = summarized_property('expats')

    def aggregate_results(self, attribute):
        """ Gets the sum of the given attribute from the results. """

        return sum(getattr(ballot, attribute) for ballot in self.ballots)

    @staticmethod
    def aggregate_results_expression(cls, attribute):
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """

        expr = select([func.sum(getattr(Ballot, attribute))])
        expr = expr.where(Ballot.vote_id == cls.id)
        expr = expr.label(attribute)

        return expr

    @hybrid_property
    def last_ballot_change(self):
        """ Returns last change of the vote, its ballots and any of its
        results.

        """
        changes = [ballot.last_change for ballot in self.ballots]
        changes = [change for change in changes if change]
        return max(changes) if changes else None

    @last_ballot_change.expression  # type:ignore[no-redef]
    def last_ballot_change(cls):
        expr = select([func.max(Ballot.last_change)])
        expr = expr.where(Ballot.vote_id == cls.id)
        expr = expr.label('last_ballot_change')
        return expr

    @hybrid_property
    def last_modified(self):
        """ Returns last change of the vote, its ballots and any of its
        results.

        """
        changes = [ballot.last_change for ballot in self.ballots]
        changes.extend([self.last_change, self.last_result_change])
        changes = [change for change in changes if change]
        return max(changes) if changes else None

    @last_modified.expression  # type:ignore[no-redef]
    def last_modified(cls):
        return func.greatest(
            cls.last_change, cls.last_result_change, cls.last_ballot_change
        )

    #: may be used to store a link related to this vote
    related_link = meta_property('related_link')
    #: Additional, translatable label for the link
    related_link_label = meta_property('related_link_label')

    #: may be used to indicate that the vote contains expats as seperate
    #: resultas (typically with entity_id = 0)
    has_expats = meta_property('expats', default=False)

    #: The segment of the domain. This might be the municipality, if this is a
    #: communal vote.
    domain_segment = meta_property('domain_segment', default='')

    def clear_results(self):
        """ Clear all the results. """

        self.status = None
        self.last_result_change = None

        for ballot in self.ballots:
            ballot.clear_results()

    def export(self, locales):
        """ Returns all data connected to this vote as list with dicts.

        This is meant as a base for json/csv/excel exports. The result is
        therefore a flat list of dictionaries with repeating values to avoid
        the nesting of values. Each record in the resulting list is a single
        ballot result.

        """

        rows = []

        for ballot in self.ballots:
            for result in ballot.results:
                row = OrderedDict()

                titles = (
                    ballot.title_translations or self.title_translations or {}
                )
                for locale in locales:
                    row[f'title_{locale}'] = titles.get(locale, '')
                row['date'] = self.date.isoformat()
                row['shortcode'] = self.shortcode
                row['domain'] = self.domain
                row['status'] = self.status or 'unknown'
                row['type'] = ballot.type
                row['district'] = result.district or ''
                row['name'] = result.name
                row['entity_id'] = result.entity_id
                row['counted'] = result.counted
                row['yeas'] = result.yeas
                row['nays'] = result.nays
                row['invalid'] = result.invalid
                row['empty'] = result.empty
                row['eligible_voters'] = result.eligible_voters
                row['expats'] = result.expats or ''

                rows.append(row)

        return rows

    def export_xml(self, canton_id, domain_of_influence):
        """ Returns all data as an eCH-0252 XML. """

        polling_day = XmlDate.from_date(self.date)
        identification = self.external_id or self.id
        results = self.proposal.results.all()
        vote = VoteType(
            vote_identification=identification,
            main_vote_identification=identification,
            other_identification=[
                NamedIdType(
                    id_name='onegov',
                    id=self.id
                )
            ],
            domain_of_influence=domain_of_influence,
            polling_day=polling_day,
            vote_title_information=[
                VoteTitleInformationType(
                    language=locale,
                    vote_title=title,
                )
                for locale, title
                in self.title_translations.items()
                if title
            ],
            decisive_majority=DecisiveMajorityType.VALUE_1,
            vote_sub_type=VoteSubTypeType.VALUE_1
        )
        counting_circle_info = [
            CountingCircleInfoType(
                counting_circle=CountingCircleType(
                    counting_circle_id=(
                        result.entity_id if result.entity_id
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
            for result in results
        ]
        delivery = Delivery(
            vote_base_delivery=EventVoteBaseDeliveryType(
                canton_id=canton_id,
                polling_day=polling_day,
                vote_info=[
                    VoteInfoType(
                        vote=vote,
                        counting_circle_info=counting_circle_info
                    )
                ],
                number_of_entries=1
            )
        )
        config = SerializerConfig(pretty_print=True)
        serializer = XmlSerializer(config=config)
        return serializer.render(delivery)
