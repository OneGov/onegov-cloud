from cached_property import cached_property
from collections import OrderedDict
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON
from onegov.file import AssociatedFiles
from onegov.file import File
from onegov.file.attachments import extract_pdf_info
from onegov.swissvotes import _
from onegov.swissvotes.models.actor import Actor
from onegov.swissvotes.models.localized_file import LocalizedFile
from onegov.swissvotes.models.policy_area import PolicyArea
from onegov.swissvotes.models.region import Region
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
    """ An attachment to a vote. """

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

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        value = getattr(instance, f'_{self.name}')
        return instance.codes(self.name).get(value)


class SwissVote(Base, TimestampMixin, AssociatedFiles):

    """ A single vote as defined by the code book.

    There are a lot of columns:
    - Some general, ready to be used attributes (bfs_number, ...)
    - Encoded attributes, where the raw integer value is stored prefixed with
      an underline and the attribute returns a translatable label by using the
      ``codes`` function, e.g.  ``_legal_form``, ``legal_form`` and
      ``codes(' _legal_form')``.
    - Descriptors, easily accessible by using ``policy_areas``.
    - A lot of lazy loaded, cantonal results only used when importing/exporting
      the dataset.
    - Recommendations from different parties and assocciations. Internally
      stored as JSON and easily accessible and group by slogan with
      ``recommendations_parties``, ``recommendations_divergent_parties`` and
      ``recommendations_associations``.
    - Different localized attachments, some of them indexed for full text
      search.

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
        if attribute == 'recommendation':
            return OrderedDict((
                (1, _("Yea")),
                (2, _("Nay")),
                (3, _("None")),
                (4, _("Empty")),
                (5, _("Free vote")),
                (66, _("Neutral")),
                (9999, _("Organization no longer exists")),
                (None, _("Unknown"))
            ))

        raise RuntimeError(f"No codes avaible for '{attribute}'")

    id = Column(Integer, nullable=False, primary_key=True)

    # Formal description
    bfs_number = Column(Numeric(8, 2), nullable=False)
    date = Column(Date, nullable=False)
    decade = Column(INT4RANGE, nullable=False)
    legislation_number = Column(Integer, nullable=False)
    legislation_decade = Column(INT4RANGE, nullable=False)
    title_de = Column(Text, nullable=False)
    title_fr = Column(Text, nullable=False)
    short_title_de = Column(Text, nullable=False)
    short_title_fr = Column(Text, nullable=False)
    keyword = Column(Text)
    votes_on_same_day = Column(Integer, nullable=False)
    _legal_form = Column('legal_form', Integer, nullable=False)
    legal_form = encoded_property()
    initiator = Column(Text)
    anneepolitique = Column(Text)
    bfs_map_de = Column(Text)
    bfs_map_fr = Column(Text)

    @property
    def title(self):
        if self.session_manager.current_locale == 'fr_CH':
            return self.title_fr
        else:
            return self.title_de

    @property
    def short_title(self):
        if self.session_manager.current_locale == 'fr_CH':
            return self.short_title_fr
        else:
            return self.short_title_de

    def bfs_map(self, locale):
        """ Returns the link to the BFS map for the given locale. """

        return self.bfs_map_fr if locale == 'fr_CH' else self.bfs_map_de

    def bfs_map_host(self, locale):
        """ Returns the Host of the BFS Map link for CSP. """

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
        """ Returns the policy areas / descriptors of the vote. """

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
        """ Returns the results of all cantons. """

        result = {}
        for canton in Region.cantons():
            value = getattr(self, f'_result_{canton}_accepted')
            if value is not None:
                result.setdefault(value, []).append(Region(canton))

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
    recommendations_other_yes = Column(Text)
    recommendations_other_no = Column(Text)
    recommendations_other_free = Column(Text)
    recommendations_divergent = Column(JSON, nullable=False, default=dict)

    def get_recommendation(self, name):
        """ Get the recommendations by name. """

        recommendations = self.recommendations or {}
        return self.codes('recommendation').get(recommendations.get(name))

    def group_recommendations(self, recommendations):
        """ Group the given recommendations by slogan. """

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
        """ The recommendations of the parties grouped by slogans. """

        recommendations = self.recommendations or {}
        return self.group_recommendations((
            (Actor(name), recommendations.get(name))
            for name in Actor.parties()
        ))

    @cached_property
    def recommendations_divergent_parties(self):
        """ The divergent recommendations of the parties grouped by slogans.

        """

        recommendations = self.recommendations_divergent or {}
        return self.group_recommendations((
            (
                (Actor(name.split('_')[0]), Region(name.split('_')[1])),
                recommendation,
            )
            for name, recommendation in sorted(recommendations.items())
        ))

    @cached_property
    def recommendations_associations(self):
        """ The recommendations of the associations grouped by slogans. """

        def as_list(value, code):
            return [
                (Actor(name.strip()), code)
                for name in (value or '').split(',')
                if name.strip()
            ]

        recommendations = self.recommendations or {}
        recommendations = [
            (Actor(name), recommendations.get(name))
            for name in Actor.associations()
        ]
        recommendations.extend(as_list(self.recommendations_other_yes, 1))
        recommendations.extend(as_list(self.recommendations_other_no, 2))
        recommendations.extend(as_list(self.recommendations_other_free, 5))
        return self.group_recommendations(recommendations)

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
    national_council_share_none = Column(Numeric(13, 10))
    national_council_share_empty = Column(Numeric(13, 10))
    national_council_share_free_vote = Column(Numeric(13, 10))
    national_council_share_neutral = Column(Numeric(13, 10))
    national_council_share_unknown = Column(Numeric(13, 10))

    @cached_property
    def has_national_council_share_data(self):
        if self.national_council_election_year:
            return True
        return False

    # attachments
    voting_text = LocalizedFile()
    brief_description = LocalizedFile()
    federal_council_message = LocalizedFile()
    parliamentary_debate = LocalizedFile()
    voting_booklet = LocalizedFile()
    resolution = LocalizedFile()
    realization = LocalizedFile()
    ad_analysis = LocalizedFile()
    results_by_domain = LocalizedFile()

    # searchable attachment texts
    searchable_text_de_CH = deferred(Column(TSVECTOR))
    searchable_text_fr_CH = deferred(Column(TSVECTOR))

    indexed_files = {
        'voting_text',
        'brief_description',
        'federal_council_message',
        'parliamentary_debate',
        # we don't include the voting booklet, resolution and ad analysis
        # - they might contain other votes from the same day!
        'realization'
    }

    def vectorize_files(self):
        """ Extract the text from the indexed files and store it. """

        for locale, language in (('de_CH', 'german'), ('fr_CH', 'french')):
            files = [
                SwissVote.__dict__[file].__get_by_locale__(self, locale)
                for file in self.indexed_files
            ]
            text = ' '.join([
                extract_pdf_info(file.reference.file)[1] or ''
                for file in files if file
            ]).strip()
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
