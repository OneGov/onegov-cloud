from cached_property import cached_property
from collections import OrderedDict
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins.content import dict_property_factory
from onegov.core.orm.types import JSON
from onegov.file import AssociatedFiles
from onegov.file import File
from onegov.swissvotes import _
from onegov.swissvotes.models.actor import Actor
from onegov.swissvotes.models.canton import Canton
from onegov.swissvotes.models.localized_file import LocalizedFile
from onegov.swissvotes.models.policy_area import PolicyArea
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy_utils import observes
from sqlalchemy.dialects.postgresql import INT4RANGE
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import deferred
from urllib.parse import urlparse
from urllib.parse import urlunparse


class SwissVoteFile(File):
    __mapper_args__ = {'polymorphic_identity': 'swissvote'}


class encoded_property(object):
    """ A shorthand property to return the label of an encoded value. Requires
    the instance the have a `codes`-lookup function. Assumes that the value
    to lookup has the same name as the property prefixed with an underline.

    Example:

        class MyClass(object):
            _value = 0
            value = encoded_property()

            def codes(self, attributes):
                return {0: 'None', 1: 'One'}

    """

    def __set_name__(self, owner, name, type='INTEGER', nullable=True):
        self.name = name
        self.type = type
        self.nullable = nullable

    def __get__(self, instance, owner):
        value = getattr(instance, f'_{self.name}')
        return instance.codes(self.name).get(value)


recommendation_property = dict_property_factory('recommendations')


class SwissVote(Base, TimestampMixin, AssociatedFiles):

    """ A single vote as defined by the code book.

    Some columns are only used when importing/exporting the dataset and are
    lazy loaded.

    """

    __tablename__ = 'swissvotes'

    @staticmethod
    def codes(attribute):
        """ Returns the codes for the given attribute as defined in the code
        book.

        """
        if attribute == 'legal_form':
            return OrderedDict((
                (1, _("Mandatory referendum")),
                (2, _("Optional referendum")),
                (3, _("Popular initiative")),
                (4, _("Direct counter-proposal")),
            ))
        if attribute == 'result_cantons_accepted':
            return OrderedDict((
                (0, _("Rejected")),
                (1, _("Accepted")),
                (3, _("Majority of the cantons not necessary")),
            ))
        if attribute == 'result' or attribute.endswith('_accepted'):
            return OrderedDict((
                (0, _("Rejected")),
                (1, _("Accepted")),
            ))
        if attribute == 'department_in_charge':
            return OrderedDict((
                (1, _("Federal Department of Foreign Affairs (FDFA)")),
                (2, _("Federal Department of Home Affairs (FDHA)")),
                (3, _("Federal Department of Justice and Police (FDJP)")),
                (4, _("Federal Department of Defence, Civil Protection and "
                      "Sport (DDPS)")),
                (5, _("Federal Department of Finance (FDF)")),
                (6, _("Federal Department of Economic Affairs, Education and "
                      "Research (EAER)")),
                (7, _("Federal Department of the Environment, Transport, "
                      "Energy and Communications (DETEC)")),
                (8, _("Federal Chancellery (FCh)")),
            ))
        if attribute == 'position_federal_council':
            return OrderedDict((
                (1, _("Accepting")),
                (2, _("Rejecting")),
                (3, _("Neutral"))
            ))
        if (
            attribute == 'position_parliament'
            or attribute == 'position_national_council'
            or attribute == 'position_council_of_states'
        ):
            return OrderedDict((
                (1, _("Accepting")),
                (2, _("Rejecting")),
            ))
        if attribute.startswith('recommendation'):
            return OrderedDict((
                (1, _("Yea")),
                (2, _("Nay")),
                (3, _("None")),
                (4, _("Empty")),
                (5, _("Free vote")),
                (66, _("Neutral")),
                (9999, _("Organization no longer exists")),
            ))

        raise RuntimeError(f"No codes avaible for '{attribute}'")

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
    legal_form = encoded_property()
    initiator = Column(Text)
    anneepolitique = Column(Text)
    bfs_map_de = Column(Text)
    bfs_map_fr = Column(Text)

    def bfs_map(self, locale):
        return self.bfs_map_fr if locale == 'fr_CH' else self.bfs_map_de

    def bfs_map_host(self, locale):
        try:
            return urlunparse(
                list(urlparse(self.bfs_map(locale))[:2]) + ['', '', '', '']
            )
        except ValueError:
            pass

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

    # Result
    _result = Column('result', Integer)
    result = encoded_property()
    result_eligible_voters = deferred(Column(Integer), group='dataset')
    result_votes_empty = deferred(Column(Integer), group='dataset')
    result_votes_invalid = deferred(Column(Integer), group='dataset')
    result_votes_valid = deferred(Column(Integer), group='dataset')
    result_votes_total = deferred(Column(Integer), group='dataset')
    result_turnout = Column(Numeric(13, 10))

    _result_people_accepted = Column('result_people_accepted', Integer)
    result_people_accepted = encoded_property()
    result_people_yeas = Column(Integer)
    result_people_nays = Column(Integer)
    result_people_yeas_p = Column(Numeric(13, 10))

    _result_cantons_accepted = Column('result_cantons_accepted', Integer)
    result_cantons_accepted = encoded_property()
    result_cantons_yeas = Column(Numeric(3, 1))
    result_cantons_nays = Column(Numeric(3, 1))
    result_cantons_yeas_p = Column(Numeric(13, 10))

    _result_ag_accepted = Column('result_ag_accepted', Integer)
    result_ag_accepted = encoded_property()
    result_ag_eligible_voters = deferred(Column(Integer), group='dataset')
    result_ag_votes_valid = deferred(Column(Integer), group='dataset')
    result_ag_votes_total = deferred(Column(Integer), group='dataset')
    result_ag_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_ag_yeas = deferred(Column(Integer), group='dataset')
    result_ag_nays = deferred(Column(Integer), group='dataset')
    result_ag_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_ai_accepted = Column('result_ai_accepted', Integer)
    result_ai_accepted = encoded_property()
    result_ai_eligible_voters = deferred(Column(Integer), group='dataset')
    result_ai_votes_valid = deferred(Column(Integer), group='dataset')
    result_ai_votes_total = deferred(Column(Integer), group='dataset')
    result_ai_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_ai_yeas = deferred(Column(Integer), group='dataset')
    result_ai_nays = deferred(Column(Integer), group='dataset')
    result_ai_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_ar_accepted = Column('result_ar_accepted', Integer)
    result_ar_accepted = encoded_property()
    result_ar_eligible_voters = deferred(Column(Integer), group='dataset')
    result_ar_votes_valid = deferred(Column(Integer), group='dataset')
    result_ar_votes_total = deferred(Column(Integer), group='dataset')
    result_ar_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_ar_yeas = deferred(Column(Integer), group='dataset')
    result_ar_nays = deferred(Column(Integer), group='dataset')
    result_ar_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_be_accepted = Column('result_be_accepted', Integer)
    result_be_accepted = encoded_property()
    result_be_eligible_voters = deferred(Column(Integer), group='dataset')
    result_be_votes_valid = deferred(Column(Integer), group='dataset')
    result_be_votes_total = deferred(Column(Integer), group='dataset')
    result_be_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_be_yeas = deferred(Column(Integer), group='dataset')
    result_be_nays = deferred(Column(Integer), group='dataset')
    result_be_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_bl_accepted = Column('result_bl_accepted', Integer)
    result_bl_accepted = encoded_property()
    result_bl_eligible_voters = deferred(Column(Integer), group='dataset')
    result_bl_votes_valid = deferred(Column(Integer), group='dataset')
    result_bl_votes_total = deferred(Column(Integer), group='dataset')
    result_bl_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_bl_yeas = deferred(Column(Integer), group='dataset')
    result_bl_nays = deferred(Column(Integer), group='dataset')
    result_bl_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_bs_accepted = Column('result_bs_accepted', Integer)
    result_bs_accepted = encoded_property()
    result_bs_eligible_voters = deferred(Column(Integer), group='dataset')
    result_bs_votes_valid = deferred(Column(Integer), group='dataset')
    result_bs_votes_total = deferred(Column(Integer), group='dataset')
    result_bs_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_bs_yeas = deferred(Column(Integer), group='dataset')
    result_bs_nays = deferred(Column(Integer), group='dataset')
    result_bs_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_fr_accepted = Column('result_fr_accepted', Integer)
    result_fr_accepted = encoded_property()
    result_fr_eligible_voters = deferred(Column(Integer), group='dataset')
    result_fr_votes_valid = deferred(Column(Integer), group='dataset')
    result_fr_votes_total = deferred(Column(Integer), group='dataset')
    result_fr_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_fr_yeas = deferred(Column(Integer), group='dataset')
    result_fr_nays = deferred(Column(Integer), group='dataset')
    result_fr_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_ge_accepted = Column('result_ge_accepted', Integer)
    result_ge_accepted = encoded_property()
    result_ge_eligible_voters = deferred(Column(Integer), group='dataset')
    result_ge_votes_valid = deferred(Column(Integer), group='dataset')
    result_ge_votes_total = deferred(Column(Integer), group='dataset')
    result_ge_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_ge_yeas = deferred(Column(Integer), group='dataset')
    result_ge_nays = deferred(Column(Integer), group='dataset')
    result_ge_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_gl_accepted = Column('result_gl_accepted', Integer)
    result_gl_accepted = encoded_property()
    result_gl_eligible_voters = deferred(Column(Integer), group='dataset')
    result_gl_votes_valid = deferred(Column(Integer), group='dataset')
    result_gl_votes_total = deferred(Column(Integer), group='dataset')
    result_gl_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_gl_yeas = deferred(Column(Integer), group='dataset')
    result_gl_nays = deferred(Column(Integer), group='dataset')
    result_gl_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_gr_accepted = Column('result_gr_accepted', Integer)
    result_gr_accepted = encoded_property()
    result_gr_eligible_voters = deferred(Column(Integer), group='dataset')
    result_gr_votes_valid = deferred(Column(Integer), group='dataset')
    result_gr_votes_total = deferred(Column(Integer), group='dataset')
    result_gr_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_gr_yeas = deferred(Column(Integer), group='dataset')
    result_gr_nays = deferred(Column(Integer), group='dataset')
    result_gr_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_ju_accepted = Column('result_ju_accepted', Integer)
    result_ju_accepted = encoded_property()
    result_ju_eligible_voters = deferred(Column(Integer), group='dataset')
    result_ju_votes_valid = deferred(Column(Integer), group='dataset')
    result_ju_votes_total = deferred(Column(Integer), group='dataset')
    result_ju_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_ju_yeas = deferred(Column(Integer), group='dataset')
    result_ju_nays = deferred(Column(Integer), group='dataset')
    result_ju_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_lu_accepted = Column('result_lu_accepted', Integer)
    result_lu_accepted = encoded_property()
    result_lu_eligible_voters = deferred(Column(Integer), group='dataset')
    result_lu_votes_valid = deferred(Column(Integer), group='dataset')
    result_lu_votes_total = deferred(Column(Integer), group='dataset')
    result_lu_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_lu_yeas = deferred(Column(Integer), group='dataset')
    result_lu_nays = deferred(Column(Integer), group='dataset')
    result_lu_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_ne_accepted = Column('result_ne_accepted', Integer)
    result_ne_accepted = encoded_property()
    result_ne_eligible_voters = deferred(Column(Integer), group='dataset')
    result_ne_votes_valid = deferred(Column(Integer), group='dataset')
    result_ne_votes_total = deferred(Column(Integer), group='dataset')
    result_ne_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_ne_yeas = deferred(Column(Integer), group='dataset')
    result_ne_nays = deferred(Column(Integer), group='dataset')
    result_ne_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_nw_accepted = Column('result_nw_accepted', Integer)
    result_nw_accepted = encoded_property()
    result_nw_eligible_voters = deferred(Column(Integer), group='dataset')
    result_nw_votes_valid = deferred(Column(Integer), group='dataset')
    result_nw_votes_total = deferred(Column(Integer), group='dataset')
    result_nw_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_nw_yeas = deferred(Column(Integer), group='dataset')
    result_nw_nays = deferred(Column(Integer), group='dataset')
    result_nw_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_ow_accepted = Column('result_ow_accepted', Integer)
    result_ow_accepted = encoded_property()
    result_ow_eligible_voters = deferred(Column(Integer), group='dataset')
    result_ow_votes_valid = deferred(Column(Integer), group='dataset')
    result_ow_votes_total = deferred(Column(Integer), group='dataset')
    result_ow_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_ow_yeas = deferred(Column(Integer), group='dataset')
    result_ow_nays = deferred(Column(Integer), group='dataset')
    result_ow_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_sg_accepted = Column('result_sg_accepted', Integer)
    result_sg_accepted = encoded_property()
    result_sg_eligible_voters = deferred(Column(Integer), group='dataset')
    result_sg_votes_valid = deferred(Column(Integer), group='dataset')
    result_sg_votes_total = deferred(Column(Integer), group='dataset')
    result_sg_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_sg_yeas = deferred(Column(Integer), group='dataset')
    result_sg_nays = deferred(Column(Integer), group='dataset')
    result_sg_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_sh_accepted = Column('result_sh_accepted', Integer)
    result_sh_accepted = encoded_property()
    result_sh_eligible_voters = deferred(Column(Integer), group='dataset')
    result_sh_votes_valid = deferred(Column(Integer), group='dataset')
    result_sh_votes_total = deferred(Column(Integer), group='dataset')
    result_sh_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_sh_yeas = deferred(Column(Integer), group='dataset')
    result_sh_nays = deferred(Column(Integer), group='dataset')
    result_sh_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_so_accepted = Column('result_so_accepted', Integer)
    result_so_accepted = encoded_property()
    result_so_eligible_voters = deferred(Column(Integer), group='dataset')
    result_so_votes_valid = deferred(Column(Integer), group='dataset')
    result_so_votes_total = deferred(Column(Integer), group='dataset')
    result_so_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_so_yeas = deferred(Column(Integer), group='dataset')
    result_so_nays = deferred(Column(Integer), group='dataset')
    result_so_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_sz_accepted = Column('result_sz_accepted', Integer)
    result_sz_accepted = encoded_property()
    result_sz_eligible_voters = deferred(Column(Integer), group='dataset')
    result_sz_votes_valid = deferred(Column(Integer), group='dataset')
    result_sz_votes_total = deferred(Column(Integer), group='dataset')
    result_sz_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_sz_yeas = deferred(Column(Integer), group='dataset')
    result_sz_nays = deferred(Column(Integer), group='dataset')
    result_sz_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_tg_accepted = Column('result_tg_accepted', Integer)
    result_tg_accepted = encoded_property()
    result_tg_eligible_voters = deferred(Column(Integer), group='dataset')
    result_tg_votes_valid = deferred(Column(Integer), group='dataset')
    result_tg_votes_total = deferred(Column(Integer), group='dataset')
    result_tg_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_tg_yeas = deferred(Column(Integer), group='dataset')
    result_tg_nays = deferred(Column(Integer), group='dataset')
    result_tg_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_ti_accepted = Column('result_ti_accepted', Integer)
    result_ti_accepted = encoded_property()
    result_ti_eligible_voters = deferred(Column(Integer), group='dataset')
    result_ti_votes_valid = deferred(Column(Integer), group='dataset')
    result_ti_votes_total = deferred(Column(Integer), group='dataset')
    result_ti_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_ti_yeas = deferred(Column(Integer), group='dataset')
    result_ti_nays = deferred(Column(Integer), group='dataset')
    result_ti_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_ur_accepted = Column('result_ur_accepted', Integer)
    result_ur_accepted = encoded_property()
    result_ur_eligible_voters = deferred(Column(Integer), group='dataset')
    result_ur_votes_valid = deferred(Column(Integer), group='dataset')
    result_ur_votes_total = deferred(Column(Integer), group='dataset')
    result_ur_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_ur_yeas = deferred(Column(Integer), group='dataset')
    result_ur_nays = deferred(Column(Integer), group='dataset')
    result_ur_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_vd_accepted = Column('result_vd_accepted', Integer)
    result_vd_accepted = encoded_property()
    result_vd_eligible_voters = deferred(Column(Integer), group='dataset')
    result_vd_votes_valid = deferred(Column(Integer), group='dataset')
    result_vd_votes_total = deferred(Column(Integer), group='dataset')
    result_vd_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_vd_yeas = deferred(Column(Integer), group='dataset')
    result_vd_nays = deferred(Column(Integer), group='dataset')
    result_vd_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_vs_accepted = Column('result_vs_accepted', Integer)
    result_vs_accepted = encoded_property()
    result_vs_eligible_voters = deferred(Column(Integer), group='dataset')
    result_vs_votes_valid = deferred(Column(Integer), group='dataset')
    result_vs_votes_total = deferred(Column(Integer), group='dataset')
    result_vs_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_vs_yeas = deferred(Column(Integer), group='dataset')
    result_vs_nays = deferred(Column(Integer), group='dataset')
    result_vs_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_zg_accepted = Column('result_zg_accepted', Integer)
    result_zg_accepted = encoded_property()
    result_zg_eligible_voters = deferred(Column(Integer), group='dataset')
    result_zg_votes_valid = deferred(Column(Integer), group='dataset')
    result_zg_votes_total = deferred(Column(Integer), group='dataset')
    result_zg_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_zg_yeas = deferred(Column(Integer), group='dataset')
    result_zg_nays = deferred(Column(Integer), group='dataset')
    result_zg_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    _result_zh_accepted = Column('result_zh_accepted', Integer)
    result_zh_accepted = encoded_property()
    result_zh_eligible_voters = deferred(Column(Integer), group='dataset')
    result_zh_votes_valid = deferred(Column(Integer), group='dataset')
    result_zh_votes_total = deferred(Column(Integer), group='dataset')
    result_zh_turnout = deferred(Column(Numeric(13, 10)), group='dataset')
    result_zh_yeas = deferred(Column(Integer), group='dataset')
    result_zh_nays = deferred(Column(Integer), group='dataset')
    result_zh_yeas_p = deferred(Column(Numeric(13, 10)), group='dataset')

    @cached_property
    def results_cantons(self):
        result = {}
        for canton in Canton.abbreviations():
            value = getattr(self, f'_result_{canton}_accepted')
            if value is not None:
                result.setdefault(value, []).append(Canton(canton))

        codes = self.codes('result_accepted')
        return OrderedDict([
            (codes[key], result[key])
            for key in sorted(result.keys())
        ])

    # Authorities
    _department_in_charge = Column('department_in_charge', Integer)
    department_in_charge = encoded_property()
    procedure_number = Column(Numeric(8, 3))
    _position_federal_council = Column('position_federal_council', Integer)
    position_federal_council = encoded_property()
    _position_parliament = Column('position_parliament', Integer)
    position_parliament = encoded_property()
    _position_national_council = Column('position_national_council', Integer)
    position_national_council = encoded_property()
    position_national_council_yeas = Column(Integer)
    position_national_council_nays = Column(Integer)
    _position_council_of_states = Column('position_council_of_states', Integer)
    position_council_of_states = encoded_property()
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
    recommendations = Column(JSON, nullable=False, default=dict)
    _recommendation_bdp = recommendation_property('bdp')
    _recommendation_csp = recommendation_property('csp')
    _recommendation_cvp = recommendation_property('cvp')
    _recommendation_edu = recommendation_property('edu')
    _recommendation_evp = recommendation_property('evp')
    _recommendation_fdp = recommendation_property('fdp')
    _recommendation_fps = recommendation_property('fps')
    _recommendation_glp = recommendation_property('glp')
    _recommendation_gps = recommendation_property('gps')
    _recommendation_kvp = recommendation_property('kvp')
    _recommendation_ldu = recommendation_property('ldu')
    _recommendation_lega = recommendation_property('lega')
    _recommendation_lps = recommendation_property('lps')
    _recommendation_mcg = recommendation_property('mcg')
    _recommendation_pda = recommendation_property('pda')
    _recommendation_poch = recommendation_property('poch')
    _recommendation_rep = recommendation_property('rep')
    _recommendation_sd = recommendation_property('sd')
    _recommendation_sps = recommendation_property('sps')
    _recommendation_svp = recommendation_property('svp')
    recommendation_bdp = encoded_property()
    recommendation_csp = encoded_property()
    recommendation_cvp = encoded_property()
    recommendation_edu = encoded_property()
    recommendation_evp = encoded_property()
    recommendation_fdp = encoded_property()
    recommendation_fps = encoded_property()
    recommendation_glp = encoded_property()
    recommendation_gps = encoded_property()
    recommendation_kvp = encoded_property()
    recommendation_ldu = encoded_property()
    recommendation_lega = encoded_property()
    recommendation_lps = encoded_property()
    recommendation_mcg = encoded_property()
    recommendation_pda = encoded_property()
    recommendation_poch = encoded_property()
    recommendation_rep = encoded_property()
    recommendation_sd = encoded_property()
    recommendation_sps = encoded_property()
    recommendation_svp = encoded_property()

    def group_recommendations(self, recommendations):
        result = {}
        for actor, recommendation in recommendations:
            if recommendation is not None and recommendation != 9999:
                result.setdefault(recommendation, []).append(actor)

        codes = self.codes('recommendation')
        return OrderedDict([
            (codes[key], result[key])
            for key in sorted(result.keys())
        ])

    @cached_property
    def recommendations_parties(self):
        return self.group_recommendations((
            (Actor('bdp'), self._recommendation_bdp),
            (Actor('csp'), self._recommendation_csp),
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
        ))

    _recommendation_acs = recommendation_property('acs')
    _recommendation_bpuk = recommendation_property('bpuk')
    _recommendation_eco = recommendation_property('eco')
    _recommendation_edk = recommendation_property('edk')
    _recommendation_endk = recommendation_property('endk')
    _recommendation_fdk = recommendation_property('fdk')
    _recommendation_gdk = recommendation_property('gdk')
    _recommendation_gem = recommendation_property('gem')
    _recommendation_kdk = recommendation_property('kdk')
    _recommendation_kkjpd = recommendation_property('kkjpd')
    _recommendation_ldk = recommendation_property('ldk')
    _recommendation_sav = recommendation_property('sav')
    _recommendation_sbk = recommendation_property('sbk')
    _recommendation_sbv_usp = recommendation_property('sbv_usp')
    _recommendation_sgb = recommendation_property('sgb')
    _recommendation_sgv = recommendation_property('sgv')
    _recommendation_sodk = recommendation_property('sodk')
    _recommendation_ssv = recommendation_property('ssv')
    _recommendation_tcs = recommendation_property('tcs')
    _recommendation_travs = recommendation_property('travs')
    _recommendation_vcs = recommendation_property('vcs')
    _recommendation_vdk = recommendation_property('vdk')
    _recommendation_voev = recommendation_property('voev')
    _recommendation_vpod = recommendation_property('vpod')
    _recommendation_vsa = recommendation_property('vsa')

    recommendation_acs = encoded_property()
    recommendation_bpuk = encoded_property()
    recommendation_eco = encoded_property()
    recommendation_edk = encoded_property()
    recommendation_endk = encoded_property()
    recommendation_fdk = encoded_property()
    recommendation_gdk = encoded_property()
    recommendation_gem = encoded_property()
    recommendation_kdk = encoded_property()
    recommendation_kkjpd = encoded_property()
    recommendation_ldk = encoded_property()
    recommendation_sav = encoded_property()
    recommendation_sbk = encoded_property()
    recommendation_sbv_usp = encoded_property()
    recommendation_sgb = encoded_property()
    recommendation_sgv = encoded_property()
    recommendation_sodk = encoded_property()
    recommendation_ssv = encoded_property()
    recommendation_tcs = encoded_property()
    recommendation_travs = encoded_property()
    recommendation_vcs = encoded_property()
    recommendation_vdk = encoded_property()
    recommendation_voev = encoded_property()
    recommendation_vpod = encoded_property()
    recommendation_vsa = encoded_property()

    @cached_property
    def recommendations_associations(self):
        return self.group_recommendations((
            (Actor('acs'), self._recommendation_acs),
            (Actor('bpuk'), self._recommendation_bpuk),
            (Actor('eco'), self._recommendation_eco),
            (Actor('edk'), self._recommendation_edk),
            (Actor('endk'), self._recommendation_endk),
            (Actor('fdk'), self._recommendation_fdk),
            (Actor('gdk'), self._recommendation_gdk),
            (Actor('gem'), self._recommendation_gem),
            (Actor('kdk'), self._recommendation_kdk),
            (Actor('kkjpd'), self._recommendation_kkjpd),
            (Actor('ldk'), self._recommendation_ldk),
            (Actor('sav'), self._recommendation_sav),
            (Actor('sbk'), self._recommendation_sbk),
            (Actor('sbv-usp'), self._recommendation_sbv_usp),
            (Actor('sgb'), self._recommendation_sgb),
            (Actor('sgv'), self._recommendation_sgv),
            (Actor('sodk'), self._recommendation_sodk),
            (Actor('ssv'), self._recommendation_ssv),
            (Actor('tcs'), self._recommendation_tcs),
            (Actor('travs'), self._recommendation_travs),
            (Actor('vcs'), self._recommendation_vcs),
            (Actor('vdk'), self._recommendation_vdk),
            (Actor('voev'), self._recommendation_voev),
            (Actor('vpod'), self._recommendation_vpod),
            (Actor('vsa'), self._recommendation_vsa),
        ))

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
    def has_national_council_share_data(self):
        if self.national_council_election_year:
            return True
        return False

    # attachments
    voting_text = LocalizedFile()
    federal_council_message = LocalizedFile()
    parliamentary_debate = LocalizedFile()
    voting_booklet = LocalizedFile()
    resolution = LocalizedFile()
    realization = LocalizedFile()
    ad_analysis = LocalizedFile()
    results_by_domain = LocalizedFile()

    # searchable attachment texts
    searchable_text_de_CH = Column(TSVECTOR)
    searchable_text_fr_CH = Column(TSVECTOR)

    indexed_files = {
        'voting_text',
        'federal_council_message',
        'parliamentary_debate',
        # we don't include the voting booklet, resolution and ad analysis
        # - they might contain other votes from the same day!
        'realization'
    }

    def vectorize_files(self):
        for locale, language in (('de_CH', 'german'), ('fr_CH', 'french')):
            files = [
                SwissVote.__dict__[file].__get_by_locale__(self, locale)
                for file in self.indexed_files
            ]
            text = ' '.join([f.extract or '' for f in files if f]).strip()
            if text:
                setattr(
                    self,
                    f'searchable_text_{locale}',
                    func.to_tsvector(language, text)
                )

    @observes('files')
    def files_observer(self, files):
        self.vectorize_files()

    def get_file(self, name):
        """ Returns the requested localized file, falls back to the default
        locale.

        """
        fallback = SwissVote.__dict__.get(name).__get_by_locale__(
            self, self.session_manager.default_locale
        )
        return getattr(self, name, None) or fallback

    @property
    def percentages(self):
        """ Returns the positions and results as percentages. """

        def lookup(percentage=None, yeas=None, nays=None, code=None):
            if percentage is not None:
                return round(float(percentage), 1)
            if yeas is not None and nays is not None and (yeas and nays):
                return round(100 * (yeas / (yeas + nays)), 1)
            if code is not None:
                return {0: 0.0, 1: 100.0, 2: 0.0, 3: None}.get(code)
            return None

        result = OrderedDict()
        result[_("Federal Council")] = lookup(
            code=self._position_federal_council
        )
        result[_("National Council")] = lookup(
            yeas=self.position_national_council_yeas,
            nays=self.position_national_council_nays,
            code=self._position_national_council
        )
        result[_("Council of States")] = lookup(
            yeas=self.position_council_of_states_yeas,
            nays=self.position_council_of_states_nays,
            code=self._position_council_of_states
        )
        result[_("Yes Camp")] = lookup(
            percentage=self.national_council_share_yeas
        )
        result[_("People")] = lookup(
            percentage=self.result_people_yeas_p,
            code=self._result_people_accepted
        )
        result[_("Cantons")] = lookup(
            code=self._result_cantons_accepted,
            percentage=self.result_cantons_yeas_p,
            yeas=self.result_cantons_yeas,
            nays=self.result_cantons_nays
        )

        return result
