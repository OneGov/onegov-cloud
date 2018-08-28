from cached_property import cached_property
from collections import OrderedDict
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.file import AssociatedFiles
from onegov.file import File
from onegov.swissvotes import _
from onegov.swissvotes.models import PolicyArea
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import INT4RANGE


LEGAL_FORM = {
    1: _("Mandatory referendum"),
    2: _("Optional referendum"),
    3: _("Popular vote"),
    4: _("Direct counter-proposal"),
}

RESULT = {
    0: _("Rejected"),
    1: _("Accepted"),
}

RESULT_PEOPLE_ACCEPTED = {
    0: _("Rejected"),
    1: _("Accepted"),
}

RESULT_CANTONS_ACCEPTED = {
    0: _("Rejected"),
    1: _("Accepted"),
    3: _("Majority of the cantons not necessary"),
}

DEPARTMENT_IN_CHARGE = {
    1: _("Federal Department of Foreign Affairs (FDFA)"),
    2: _("Federal Department of Home Affairs (FDHA)"),
    3: _("Federal Department of Justice and Police (FDJP)"),
    4: _("Federal Department of Defence, Civil Protection and Sport (DDPS)"),
    5: _("Federal Department of Finance (FDF)"),
    6: _("Federal Department of Economic Affairs, Education and Research "
         "(EAER)"),
    7: _("Federal Department of the Environment, Transport, Energy and "
         "Communications (DETEC)"),
    8: _("Federal Chancellery (FCh)"),
}

POSITION_FEDERAL_COUNCIL = {
    1: _("Accepting"),
    2: _("Rejecting"),
    3: _("Neutral")
}

POSITION_PARLIAMENT = {
    1: _("Accepting"),
    2: _("Rejecting"),
}

RECOMMENDATION = {
    1: _("Yea"),
    2: _("Nay"),
    3: _("None"),
    4: _("Empty"),
    5: _("Free vote"),
    66: _("Neutral"),
    9999: _("Organization no longer exists"),
}


class SwissVoteFile(File):
    __mapper_args__ = {'polymorphic_identity': 'swissvote'}


class SwissVote(Base, TimestampMixin, AssociatedFiles):

    """ A single vote as defined by the code book. """

    __tablename__ = 'swissvotes'

    id = Column(Integer, nullable=False, primary_key=True)

    # Formal description
    bfs_number = Column(Numeric(8, 2), nullable=False)
    date = Column(Date, nullable=False)
    decade = Column(INT4RANGE, nullable=False)
    legislation_number = Column(Integer, nullable=False)
    legislation_decade = Column(INT4RANGE, nullable=False)
    title = Column(Text, nullable=False)
    keyword = Column(Text)
    votes_on_same_day = Column(Integer, nullable=False)
    _legal_form = Column('legal_form', Integer, nullable=False)
    initiator = Column(Text)
    anneepolitique = Column(Text)

    # Descriptor
    descriptor_1_level_1 = Column(Numeric(8, 4))
    descriptor_1_level_2 = Column(Numeric(8, 4))
    descriptor_1_level_3 = Column(Numeric(8, 4))
    descriptor_2_level_1 = Column(Numeric(8, 4))
    descriptor_2_level_2 = Column(Numeric(8, 4))
    descriptor_2_level_3 = Column(Numeric(8, 4))
    descriptor_3_level_1 = Column(Numeric(8, 4))
    descriptor_3_level_2 = Column(Numeric(8, 4))
    descriptor_3_level_3 = Column(Numeric(8, 4))

    # Result
    _result = Column('result', Integer)
    result_eligible_voters = Column(Integer)
    result_votes_empty = Column(Integer)
    result_votes_invalid = Column(Integer)
    result_votes_valid = Column(Integer)
    result_votes_total = Column(Integer)
    result_turnout = Column(Numeric(13, 10))
    _result_people_accepted = Column('result_people_accepted', Integer)
    result_people_yeas = Column(Integer)
    result_people_nays = Column(Integer)
    result_people_yeas_p = Column(Numeric(13, 10))
    _result_cantons_accepted = Column('result_cantons_accepted', Integer)
    result_cantons_yeas = Column(Numeric(3, 1))
    result_cantons_nays = Column(Numeric(3, 1))
    result_cantons_yeas_p = Column(Numeric(13, 10))

    # Authorities
    _department_in_charge = Column('department_in_charge', Integer)
    procedure_number = Column(Numeric(8, 3))
    _position_federal_council = Column('position_federal_council', Integer)
    _position_parliament = Column('position_parliament', Integer)
    position_national_council_yeas = Column(Integer)
    position_national_council_nays = Column(Integer)
    position_council_of_states_yeas = Column(Integer)
    position_council_of_states_nays = Column(Integer)

    # Duration
    duration_federal_assembly = Column(Integer)
    duration_post_federal_assembly = Column(Integer)
    duration_initative_collection = Column(Integer)
    duration_initative_federal_council = Column(Integer)
    duration_initative_total = Column(Integer)
    duration_referendum_collection = Column(Integer)
    duration_referendum_total = Column(Integer)
    signatures_valid = Column(Integer)
    signatures_invalid = Column(Integer)

    # Voting recommendations
    _recommendation_fdp = Column('recommendation_fdp', Integer)
    _recommendation_cvp = Column('recommendation_cvp', Integer)
    _recommendation_sps = Column('recommendation_sps', Integer)
    _recommendation_svp = Column('recommendation_svp', Integer)
    _recommendation_lps = Column('recommendation_lps', Integer)
    _recommendation_ldu = Column('recommendation_ldu', Integer)
    _recommendation_evp = Column('recommendation_evp', Integer)
    _recommendation_ucsp = Column('recommendation_ucsp', Integer)
    _recommendation_pda = Column('recommendation_pda', Integer)
    _recommendation_poch = Column('recommendation_poch', Integer)
    _recommendation_gps = Column('recommendation_gps', Integer)
    _recommendation_sd = Column('recommendation_sd', Integer)
    _recommendation_rep = Column('recommendation_rep', Integer)
    _recommendation_edu = Column('recommendation_edu', Integer)
    _recommendation_fps = Column('recommendation_fps', Integer)
    _recommendation_lega = Column('recommendation_lega', Integer)
    _recommendation_kvp = Column('recommendation_kvp', Integer)
    _recommendation_glp = Column('recommendation_glp', Integer)
    _recommendation_bdp = Column('recommendation_bdp', Integer)
    _recommendation_mcg = Column('recommendation_mcg', Integer)

    _recommendation_zsa = Column('recommendation_zsa', Integer)
    _recommendation_eco = Column('recommendation_eco', Integer)
    _recommendation_sgv = Column('recommendation_sgv', Integer)
    _recommendation_sbv = Column('recommendation_sbv', Integer)
    _recommendation_sgb = Column('recommendation_sgb', Integer)
    _recommendation_cng_travs = Column('recommendation_cng_travs', Integer)
    _recommendation_vsa = Column('recommendation_vsa', Integer)

    # Electoral strength
    national_council_election_year = Column(Integer)
    national_council_share_fdp = Column(Numeric(13, 10))
    national_council_share_cvp = Column(Numeric(13, 10))
    national_council_share_sp = Column(Numeric(13, 10))
    national_council_share_svp = Column(Numeric(13, 10))
    national_council_share_lps = Column(Numeric(13, 10))
    national_council_share_ldu = Column(Numeric(13, 10))
    national_council_share_evp = Column(Numeric(13, 10))
    national_council_share_csp = Column(Numeric(13, 10))
    national_council_share_pda = Column(Numeric(13, 10))
    national_council_share_poch = Column(Numeric(13, 10))
    national_council_share_gps = Column(Numeric(13, 10))
    national_council_share_sd = Column(Numeric(13, 10))
    national_council_share_rep = Column(Numeric(13, 10))
    national_council_share_edu = Column(Numeric(13, 10))
    national_council_share_fps = Column(Numeric(13, 10))
    national_council_share_lega = Column(Numeric(13, 10))
    national_council_share_kvp = Column(Numeric(13, 10))
    national_council_share_glp = Column(Numeric(13, 10))
    national_council_share_bdp = Column(Numeric(13, 10))
    national_council_share_mcg = Column(Numeric(13, 10))
    national_council_share_ubrige = Column(Numeric(13, 10))
    national_council_share_yeas = Column(Numeric(13, 10))
    national_council_share_nays = Column(Numeric(13, 10))
    national_council_share_neutral = Column(Numeric(13, 10))
    national_council_share_vague = Column(Numeric(13, 10))

    @cached_property
    def legal_form(self):
        return LEGAL_FORM.get(self._legal_form, "")

    @cached_property
    def policy_areas(self):
        def get_level(number, level):
            value = getattr(self, f'descriptor_{number}_level_{level}')
            if value is not None:
                return PolicyArea(value, level)

        result = []
        for number in (1, 2, 3):
            for level in (3, 2, 1):
                area = get_level(number, level)
                if area:
                    result.append(area)
                    break
        return result

    @cached_property
    def department_in_charge(self):
        return DEPARTMENT_IN_CHARGE.get(self._department_in_charge, "")

    @cached_property
    def result(self):
        return RESULT.get(self._result, "")

    @cached_property
    def result_people_accepted(self):
        return RESULT_PEOPLE_ACCEPTED.get(self._result_people_accepted, "")

    @cached_property
    def result_cantons_accepted(self):
        return RESULT_CANTONS_ACCEPTED.get(self._result_cantons_accepted, "")

    @cached_property
    def position_federal_council(self):
        return POSITION_FEDERAL_COUNCIL.get(self._position_federal_council, "")

    @cached_property
    def position_parliament(self):
        return POSITION_PARLIAMENT.get(self._position_parliament, "")

    def position_by_votes(self, attribute):
        yeas = getattr(self, f'{attribute}_yeas')
        nays = getattr(self, f'{attribute}_nays')
        if yeas is None or nays is None:
            return ""
        if yeas == nays:
            return _("Neutral")
        if yeas > nays:
            return _("Accepting")
        return _("Rejecting")

    @cached_property
    def position_national_council(self):
        return self.position_by_votes('position_national_council')

    @cached_property
    def position_council_of_states(self):
        return self.position_by_votes('position_council_of_states')

    def group_recommendations(self, recommendations):
        result = {}
        for key, value in recommendations.items():
            if value is not None and value != 9999:
                result.setdefault(value, []).append(key)

        return OrderedDict([
            (RECOMMENDATION[key], sorted(result[key]))
            for key in sorted(result.keys())
        ])

    @cached_property
    def recommendations_parties(self):
        return self.group_recommendations({
            'FDP': self._recommendation_fdp,
            'CVP': self._recommendation_cvp,
            'SPS': self._recommendation_sps,
            'SVP': self._recommendation_svp,
            'LPS': self._recommendation_lps,
            'LDU': self._recommendation_ldu,
            'EVP': self._recommendation_evp,
            'UCSP': self._recommendation_ucsp,
            'PdA': self._recommendation_pda,
            'POCH': self._recommendation_poch,
            'GPS': self._recommendation_gps,
            'SD': self._recommendation_sd,
            'REP': self._recommendation_rep,
            'EDU': self._recommendation_edu,
            'FPS': self._recommendation_fps,
            'Lega': self._recommendation_lega,
            'KVP': self._recommendation_kvp,
            'GLP': self._recommendation_glp,
            'BDP': self._recommendation_bdp,
            'MCG': self._recommendation_mcg,
        })

    @cached_property
    def recommendations_associations(self):
        return self.group_recommendations({
            'ZSA': self._recommendation_zsa,
            'ECO': self._recommendation_eco,
            'SGV': self._recommendation_sgv,
            'SBV': self._recommendation_sbv,
            'SGB': self._recommendation_sgb,
            'Travail.Suisse': self._recommendation_cng_travs,
            'VSA': self._recommendation_vsa,
        })

    @cached_property
    def has_national_council_share_data(self):
        if self.national_council_election_year:
            return True
        return False

    def get_attachment(self, name):
        for file in self.files:
            if file.name == name:
                return file
        return None

    def delete_attachment(self, name):
        for file in self.files:
            if file.name == name:
                self.files.remove(file)

    def set_attachment(self, name, attachment):
        assert attachment.reference.content_type == 'application/pdf'
        attachment.name = name
        self.delete_attachment(name)
        self.files.append(attachment)

    @property
    def voting_text(self):
        return self.get_attachment('voting_text')

    @voting_text.setter
    def voting_text(self, value):
        self.set_attachment('voting_text', value)

    @voting_text.deleter
    def voting_text(self):
        self.delete_attachment('voting_text')

    @property
    def federal_council_message(self):
        return self.get_attachment('federal_council_message')

    @federal_council_message.setter
    def federal_council_message(self, value):
        self.set_attachment('federal_council_message', value)

    @federal_council_message.deleter
    def federal_council_message(self):
        self.delete_attachment('federal_council_message')

    @property
    def parliamentary_debate(self):
        return self.get_attachment('parliamentary_debate')

    @parliamentary_debate.setter
    def parliamentary_debate(self, value):
        self.set_attachment('parliamentary_debate', value)

    @parliamentary_debate.deleter
    def parliamentary_debate(self):
        self.delete_attachment('parliamentary_debate')
