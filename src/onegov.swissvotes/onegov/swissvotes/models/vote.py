from cached_property import cached_property
from collections import OrderedDict
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.file import AssociatedFiles
from onegov.file import File
from onegov.search import ORMSearchable
from onegov.swissvotes import _
from onegov.swissvotes.models.actor import Actor
from onegov.swissvotes.models.policy_area import PolicyArea
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import INT4RANGE


LEGAL_FORM = {
    1: _("Mandatory referendum"),
    2: _("Optional referendum"),
    3: _("Popular initiative"),
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


class SwissVote(Base, TimestampMixin, AssociatedFiles, ORMSearchable):

    """ A single vote as defined by the code book. """

    __tablename__ = 'swissvotes'

    es_public = True
    es_properties = {
        'title': {'type': 'localized'},
        'keyword': {'type': 'localized'},
        'initiator': {'type': 'localized'},
    }

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
    _recommendation_csp = Column('recommendation_csp', Integer)
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

    _recommendation_sav = Column('recommendation_sav', Integer)
    _recommendation_eco = Column('recommendation_eco', Integer)
    _recommendation_sgv = Column('recommendation_sgv', Integer)
    _recommendation_sbv_usp = Column('recommendation_sbv_usp', Integer)
    _recommendation_sgb = Column('recommendation_sgb', Integer)
    _recommendation_travs = Column('recommendation_travs', Integer)
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
        for actor, recommendation in recommendations:
            if recommendation is not None and recommendation != 9999:
                result.setdefault(recommendation, []).append(actor)

        return OrderedDict([
            (RECOMMENDATION[key], result[key])
            for key in sorted(result.keys())
        ])

    @cached_property
    def recommendations_parties(self):
        return self.group_recommendations((
            (Actor('bdp'), self._recommendation_bdp),
            (Actor('cvp'), self._recommendation_cvp),
            (Actor('edu'), self._recommendation_edu),
            (Actor('evp'), self._recommendation_evp),
            (Actor('fdp'), self._recommendation_fdp),
            (Actor('fps'), self._recommendation_fps),
            (Actor('glp'), self._recommendation_glp),
            (Actor('gps'), self._recommendation_gps),
            (Actor('kvp'), self._recommendation_kvp),
            (Actor('ldu'), self._recommendation_ldu),
            (Actor('lega'), self._recommendation_lega),
            (Actor('lps'), self._recommendation_lps),
            (Actor('mcg'), self._recommendation_mcg),
            (Actor('pda'), self._recommendation_pda),
            (Actor('poch'), self._recommendation_poch),
            (Actor('rep'), self._recommendation_rep),
            (Actor('sd'), self._recommendation_sd),
            (Actor('sps'), self._recommendation_sps),
            (Actor('svp'), self._recommendation_svp),
            (Actor('csp'), self._recommendation_csp),
        ))

    @cached_property
    def recommendations_associations(self):
        return self.group_recommendations((
            (Actor('eco'), self._recommendation_eco),
            (Actor('sbv-usp'), self._recommendation_sbv_usp),
            (Actor('sgb'), self._recommendation_sgb),
            (Actor('sgv'), self._recommendation_sgv),
            (Actor('travs'), self._recommendation_travs),
            (Actor('vsa'), self._recommendation_vsa),
            (Actor('sav'), self._recommendation_sav),
        ))

    @cached_property
    def has_national_council_share_data(self):
        if self.national_council_election_year:
            return True
        return False

    def localized_attachment_name(self, name):
        locale = self.session_manager.current_locale
        return name if name.endswith(locale) else '{}-{}'.format(name, locale)

    def get_attachment(self, name):
        name = self.localized_attachment_name(name)
        for file in self.files:
            if file.name == name:
                return file
        return None

    def delete_attachment(self, name):
        name = self.localized_attachment_name(name)
        for file in self.files:
            if file.name == name:
                self.files.remove(file)

    def set_attachment(self, name, attachment):
        name = self.localized_attachment_name(name)
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
