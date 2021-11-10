from cached_property import cached_property
from collections import OrderedDict
from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON
from onegov.core.utils import Bunch
from onegov.pdf.utils import extract_pdf_info
from onegov.swissvotes import _
from onegov.swissvotes.models.actor import Actor
from onegov.swissvotes.models.file import FileSubCollection
from onegov.swissvotes.models.file import LocalizedFile
from onegov.swissvotes.models.file import LocalizedFiles
from onegov.swissvotes.models.policy_area import PolicyArea
from onegov.swissvotes.models.region import Region
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy_utils import observes
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import deferred
from urllib.parse import urlparse
from urllib.parse import urlunparse


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

    # todo: set _xxx attribute ourselves!

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        value = getattr(instance, f'_{self.name}')
        return instance.codes(self.name, instance.deciding_question).get(value)


class localized_property(object):
    """ A shorthand property to return a localized attribute. Requires at least
    a `xxx_de` attribute and falls back to this.

    Example:

        class MyClass(object):
            value_de = Column(Text)
            value_fr = Column(Text)
            value = localized_property()
    """
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        lang = instance.session_manager.current_locale[:2]
        attribute = f'{self.name}_{lang}'
        if hasattr(instance, attribute):
            return getattr(instance, attribute)
        return getattr(instance, f'{self.name}_de', None)


class SwissVote(Base, TimestampMixin, LocalizedFiles, ContentMixin):

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

    - Metadata from external information sources such as Museum für Gestaltung
      can be stored in the content or meta field provided by the
      ``ContentMixin``.
    """

    __tablename__ = 'swissvotes'

    ORGANIZATION_NO_LONGER_EXISTS = 9999

    @staticmethod
    def codes(attribute, deciding_question=False):
        """ Returns the codes for the given attribute as defined in the code
        book.
        deciding_question is a switch needed for three votes as of 2019.

        """

        dc = deciding_question

        if attribute == 'legal_form':
            return OrderedDict((
                (1, _("Mandatory referendum")),
                (2, _("Optional referendum")),
                (3, _("Popular initiative")),
                (4, _("Direct counter-proposal")),
                (5, _("Deciding question")),
            ))
        if attribute == 'result_cantons_accepted':
            return OrderedDict((
                (0, _("Rejected") if not dc
                    else _("Preferred the counter-proposal")),
                (1, _("Accepted") if not dc
                    else _("Preferred the popular initiative")),
                (3, _("Majority of the cantons not necessary")),
            ))

        if attribute == 'result_accepted':
            return OrderedDict((
                (0, _("Rejected") if not dc
                    else _("For the counter-proposal")),
                (1, _("Accepted") if not dc
                    else _("For the initiative")),
            ))

        if attribute == 'result' or attribute.endswith('_accepted'):
            return OrderedDict((
                (0, _("Rejected") if not dc
                    else _("Preferred the counter-proposal")),
                (1, _("Accepted") if not dc
                    else _("Preferred the popular initiative")),
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
        if (attribute == 'position_federal_council'
                or attribute == 'position_national_council'
                or attribute == 'position_council_of_states'):
            return OrderedDict((
                (1, _("Accepting") if not dc
                    else _("Preference for the popular initiative")),
                (2, _("Rejecting") if not dc
                    else _("Preference for the counter-proposal")),
                (3, _("None"))
            ))

        if attribute == 'position_parliament':
            return OrderedDict((
                (1, _("Accepting") if not dc
                    else _("Preference for the popular initiative")),
                (2, _("Rejecting") if not dc
                    else _("Preference for the counter-proposal")),
            ))
        if attribute == 'recommendation':
            # Added ordering how it should be displayed in strengths table
            return OrderedDict((
                (1, _("Preference for the popular initiative")
                    if deciding_question else _("Yea")),
                (2, _("Preference for the counter-proposal")
                    if deciding_question else _("Nay")),
                (4, _("Empty")),
                (5, _("Free vote")),
                (3, _("None")),
                (66, _("Neutral")),
                (9999, _("Organization no longer exists")),
                (None, _("unknown"))
            ))

        raise RuntimeError(f"No codes available for '{attribute}'")

    id = Column(Integer, nullable=False, primary_key=True)

    # Formal description
    bfs_number = Column(Numeric(8, 2), nullable=False)
    date = Column(Date, nullable=False)
    title_de = Column(Text, nullable=False)
    title_fr = Column(Text, nullable=False)
    title = localized_property()
    short_title_de = Column(Text, nullable=False)
    short_title_fr = Column(Text, nullable=False)
    short_title = localized_property()
    brief_description_title = Column(Text)
    keyword = Column(Text)
    _legal_form = Column('legal_form', Integer, nullable=False)
    legal_form = encoded_property()
    initiator = Column(Text)
    anneepolitique = Column(Text)
    bfs_map_de = Column(Text)
    bfs_map_fr = Column(Text)
    bfs_map = localized_property()

    @property
    def bfs_map_host(self):
        """ Returns the Host of the BFS Map link for CSP. """

        try:
            return urlunparse(list(urlparse(self.bfs_map)[:2]) + 4 * [''])
        except ValueError:
            pass

    @property
    def deciding_question(self):
        return self._legal_form == 5

    # Additional links
    link_curia_vista_de = meta_property()
    link_curia_vista_fr = meta_property()
    link_curia_vista = localized_property()
    link_bk_results_de = meta_property()
    link_bk_results_fr = meta_property()
    link_bk_results = localized_property()
    link_bk_chrono_de = meta_property()
    link_bk_chrono_fr = meta_property()
    link_bk_chrono = localized_property()
    link_federal_council_de = meta_property()
    link_federal_council_fr = meta_property()
    link_federal_council_en = meta_property()
    link_federal_council = localized_property()
    link_federal_departement_de = meta_property()
    link_federal_departement_fr = meta_property()
    link_federal_departement_en = meta_property()
    link_federal_departement = localized_property()
    link_federal_office_de = meta_property()
    link_federal_office_fr = meta_property()
    link_federal_office_en = meta_property()
    link_federal_office = localized_property()
    link_post_vote_poll_de = meta_property()
    link_post_vote_poll_fr = meta_property()
    link_post_vote_poll_en = meta_property()
    link_post_vote_poll = localized_property()

    # space-separated poster URLs coming from the dataset
    posters_mfg_yea = Column(Text)
    posters_mfg_nay = Column(Text)
    posters_sa_yea = Column(Text)
    posters_sa_nay = Column(Text)

    # Fetched list of image urls using MfG API
    posters_mfg_yea_imgs = meta_property(default=dict)
    posters_mfg_nay_imgs = meta_property(default=dict)

    # Fetched list of image urls using SA API
    posters_sa_yea_imgs = meta_property(default=dict)
    posters_sa_nay_imgs = meta_property(default=dict)

    def posters(self, request):
        result = {'yea': [], 'nay': []}
        for key, attribute, label in (
            ('yea', 'posters_mfg_yea', _('Link eMuseum.ch')),
            ('nay', 'posters_mfg_nay', _('Link eMuseum.ch')),
            ('yea', 'posters_sa_yea', _('Link Social Archives')),
            ('nay', 'posters_sa_nay', _('Link Social Archives')),
        ):
            images = getattr(self, f'{attribute}_imgs')
            urls = (getattr(self, attribute) or '').strip().split(' ')
            for url in urls:
                image = images.get(url)
                if image:
                    result[key].append(
                        Bunch(
                            thumbnail=image,
                            image=image,
                            url=url,
                            label=label
                        )
                    )

        for key, attribute, label in (
            ('yea', 'campaign_material_yea', _('Swissvotes database')),
            ('nay', 'campaign_material_nay', _('Swissvotes database')),
        ):
            for image in getattr(self, attribute):
                result[key].append(
                    Bunch(
                        thumbnail=request.link(image, 'thumbnail'),
                        image=request.link(image),
                        url=None,
                        label=label
                    )
                )
        return result

    # Media
    media_ads_total = Column(Integer)
    media_ads_yea_p = Column(Numeric(13, 10))
    media_coverage_articles_total = Column(Integer)
    media_coverage_tonality_total = Column(Numeric(13, 10))

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
    result_turnout = Column(Numeric(13, 10))
    _result_people_accepted = Column('result_people_accepted', Integer)
    result_people_accepted = encoded_property()
    result_people_yeas_p = Column(Numeric(13, 10))
    _result_cantons_accepted = Column('result_cantons_accepted', Integer)
    result_cantons_accepted = encoded_property()
    result_cantons_yeas = Column(Numeric(3, 1))
    result_cantons_nays = Column(Numeric(3, 1))
    _result_ag_accepted = Column('result_ag_accepted', Integer)
    result_ag_accepted = encoded_property()
    _result_ai_accepted = Column('result_ai_accepted', Integer)
    result_ai_accepted = encoded_property()
    _result_ar_accepted = Column('result_ar_accepted', Integer)
    result_ar_accepted = encoded_property()
    _result_be_accepted = Column('result_be_accepted', Integer)
    result_be_accepted = encoded_property()
    _result_bl_accepted = Column('result_bl_accepted', Integer)
    result_bl_accepted = encoded_property()
    _result_bs_accepted = Column('result_bs_accepted', Integer)
    result_bs_accepted = encoded_property()
    _result_fr_accepted = Column('result_fr_accepted', Integer)
    result_fr_accepted = encoded_property()
    _result_ge_accepted = Column('result_ge_accepted', Integer)
    result_ge_accepted = encoded_property()
    _result_gl_accepted = Column('result_gl_accepted', Integer)
    result_gl_accepted = encoded_property()
    _result_gr_accepted = Column('result_gr_accepted', Integer)
    result_gr_accepted = encoded_property()
    _result_ju_accepted = Column('result_ju_accepted', Integer)
    result_ju_accepted = encoded_property()
    _result_lu_accepted = Column('result_lu_accepted', Integer)
    result_lu_accepted = encoded_property()
    _result_ne_accepted = Column('result_ne_accepted', Integer)
    result_ne_accepted = encoded_property()
    _result_nw_accepted = Column('result_nw_accepted', Integer)
    result_nw_accepted = encoded_property()
    _result_ow_accepted = Column('result_ow_accepted', Integer)
    result_ow_accepted = encoded_property()
    _result_sg_accepted = Column('result_sg_accepted', Integer)
    result_sg_accepted = encoded_property()
    _result_sh_accepted = Column('result_sh_accepted', Integer)
    result_sh_accepted = encoded_property()
    _result_so_accepted = Column('result_so_accepted', Integer)
    result_so_accepted = encoded_property()
    _result_sz_accepted = Column('result_sz_accepted', Integer)
    result_sz_accepted = encoded_property()
    _result_tg_accepted = Column('result_tg_accepted', Integer)
    result_tg_accepted = encoded_property()
    _result_ti_accepted = Column('result_ti_accepted', Integer)
    result_ti_accepted = encoded_property()
    _result_ur_accepted = Column('result_ur_accepted', Integer)
    result_ur_accepted = encoded_property()
    _result_vd_accepted = Column('result_vd_accepted', Integer)
    result_vd_accepted = encoded_property()
    _result_vs_accepted = Column('result_vs_accepted', Integer)
    result_vs_accepted = encoded_property()
    _result_zg_accepted = Column('result_zg_accepted', Integer)
    result_zg_accepted = encoded_property()
    _result_zh_accepted = Column('result_zh_accepted', Integer)
    result_zh_accepted = encoded_property()

    @cached_property
    def results_cantons(self):
        """ Returns the results of all cantons. """

        result = {}
        for canton in Region.cantons():
            value = getattr(self, f'_result_{canton}_accepted')
            if value is not None:
                result.setdefault(value, []).append(Region(canton))

        codes = self.codes('result_accepted', self.deciding_question)
        return OrderedDict([
            (codes[key], result[key])
            for key in sorted(result.keys())
        ])

    # Authorities
    _department_in_charge = Column('department_in_charge', Integer)
    department_in_charge = encoded_property()  # drop
    procedure_number = Column(Text)
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
    duration_post_federal_assembly = Column(Integer)  # drop
    duration_initative_collection = Column(Integer)
    duration_initative_federal_council = Column(Integer)  # drop
    duration_initative_total = Column(Integer)  # drop
    duration_referendum_collection = Column(Integer)
    duration_referendum_total = Column(Integer)  # drop
    signatures_valid = Column(Integer)
    signatures_invalid = Column(Integer)  # drop

    # Voting recommendations
    recommendations = Column(JSON, nullable=False, default=dict)
    recommendations_other_yes = Column(Text)
    recommendations_other_no = Column(Text)
    recommendations_other_free = Column(Text)
    recommendations_divergent = Column(JSON, nullable=False, default=dict)

    def get_recommendation(self, name):
        """ Get the recommendations by name. """
        return self.codes('recommendation', self.deciding_question).get(
            self.recommendations.get(name)
        )

    def get_recommendation_of_existing_parties(self):
        """ Get only the existing parties as when this vote was conducted """
        if not self.recommendations:
            return {}
        return {
            k: v for k, v in self.recommendations.items()
            if v != self.ORGANIZATION_NO_LONGER_EXISTS
        }

    def group_recommendations(self, recommendations, ignore_unknown=False):
        """ Group the given recommendations by slogan. """

        codes = self.codes('recommendation', self.deciding_question)
        recommendation_codes = list(codes.keys())

        def by_recommendation(reco):
            return recommendation_codes.index(reco)

        result = {}
        for actor, recommendation in recommendations:
            if recommendation == self.ORGANIZATION_NO_LONGER_EXISTS:
                continue
            if ignore_unknown and recommendation is None:
                continue

            result.setdefault(recommendation, []).append(actor)

        return OrderedDict([
            (codes[key], result[key])
            for key in sorted(result.keys(), key=by_recommendation)
        ])

    @staticmethod
    def normalize_actor_share_suffix(actor):
        """
        One actor is called sps, but the table name is called
        national_council_share_sp.
        TODO: As soon as the table name is adjusted, this can be removed.
        """
        if actor == 'sps':
            return 'sp'
        return actor

    def get_actors_share(self, actor):
        assert isinstance(actor, str), 'Actor must be a string'
        attr = 'national_council_share_' + \
               self.normalize_actor_share_suffix(actor)
        return getattr(self, attr, 0) or 0

    @cached_property
    def sorted_actors_list(self):
        """
         Returns a list of actors of the current vote sorted by:

        1. codes for recommendations (strength table)
        2. by electoral share (descending)

        It filters out those parties who have no electoral share

        """
        result = []
        for slogan, actor_list in self.recommendations_parties.items():
            actors = (d.name for d in actor_list)
            # Filter out those who have None as share

            result.extend(
                sorted(actors, key=self.get_actors_share, reverse=True)
            )
        return result

    @cached_property
    def recommendations_parties(self):
        """ The recommendations of the parties grouped by slogans. """

        recommendations = self.recommendations or {}
        return self.group_recommendations((
            (Actor(name), recommendations.get(name))
            for name in Actor.parties()
        ), ignore_unknown=True)

    @cached_property
    def recommendations_divergent_parties(self, ignore_unknown=True):
        """ The divergent recommendations of the parties grouped by slogans.

        """

        recommendations = self.recommendations_divergent or {}
        return self.group_recommendations((
            (
                (Actor(name.split('_')[0]), Region(name.split('_')[1])),
                recommendation,
            )
            for name, recommendation in sorted(recommendations.items())
        ), ignore_unknown=ignore_unknown)

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
        return self.group_recommendations(recommendations, ignore_unknown=True)

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
    national_council_share_mitte = Column(Numeric(13, 10))
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
    voting_text = LocalizedFile(
        label=_('Voting text'),
        extension='pdf',
        static_views={
            'de_CH': 'abstimmungstext-de.pdf',
            'fr_CH': 'abstimmungstext-fr.pdf',
        }
    )
    brief_description = LocalizedFile(
        label=_('Brief description Swissvotes'),
        extension='pdf',
        static_views={
            'de_CH': 'kurzbeschreibung.pdf',
        }
    )
    federal_council_message = LocalizedFile(
        label=_('Federal council message'),
        extension='pdf',
        static_views={
            'de_CH': 'botschaft-de.pdf',
            'fr_CH': 'botschaft-fr.pdf',
        }
    )
    parliamentary_debate = LocalizedFile(
        label=_('Parliamentary debate'),
        extension='pdf',
        static_views={
            'de_CH': 'parlamentsberatung.pdf',
        }
    )
    voting_booklet = LocalizedFile(
        label=_('Voting booklet'),
        extension='pdf',
        static_views={
            'de_CH': 'brochure-de.pdf',
            'fr_CH': 'brochure-fr.pdf',
        }
    )
    resolution = LocalizedFile(
        label=_('Resolution'),
        extension='pdf',
        static_views={
            'de_CH': 'erwahrung-de.pdf',
            'fr_CH': 'erwahrung-fr.pdf',
        }
    )
    realization = LocalizedFile(
        label=_('Realization'),
        extension='pdf',
        static_views={
            'de_CH': 'zustandekommen-de.pdf',
            'fr_CH': 'zustandekommen-fr.pdf',
        }
    )
    ad_analysis = LocalizedFile(
        label=_('Analysis of the advertising campaign by Année Politique'),
        extension='pdf',
        static_views={
            'de_CH': 'inserateanalyse.pdf',
        }
    )
    results_by_domain = LocalizedFile(
        label=_('Result by canton, district and municipality'),
        extension='xlsx',
        static_views={
            'de_CH': 'staatsebenen.xlsx',
        }
    )
    foeg_analysis = LocalizedFile(
        label=_('Media coverage: fög analysis'),
        extension='pdf',
        static_views={
            'de_CH': 'medienanalyse.pdf',
        }
    )
    post_vote_poll = LocalizedFile(
        label=_('Full analysis of post-vote poll results'),
        extension='pdf',
        static_views={
            'de_CH': 'nachbefragung-de.pdf',
            'fr_CH': 'nachbefragung-fr.pdf',
        }
    )
    post_vote_poll_methodology = LocalizedFile(
        label=_('Questionnaire of the poll'),
        extension='pdf',
        static_views={
            'de_CH': 'nachbefragung-methode-de.pdf',
            'fr_CH': 'nachbefragung-methode-fr.pdf',
        }
    )
    post_vote_poll_dataset = LocalizedFile(
        label=_('Dataset of the post-vote poll'),
        extension='csv',
        static_views={
            'de_CH': 'nachbefragung.csv',
        }
    )
    post_vote_poll_dataset_sav = LocalizedFile(
        label=_('Dataset of the post-vote poll'),
        extension='sav',
        static_views={
            'de_CH': 'nachbefragung.sav',
        }
    )
    post_vote_poll_dataset_dta = LocalizedFile(
        label=_('Dataset of the post-vote poll'),
        extension='dta',
        static_views={
            'de_CH': 'nachbefragung.dta',
        }
    )
    post_vote_poll_codebook = LocalizedFile(
        label=_('Codebook for the post-vote poll'),
        extension='pdf',
        static_views={
            'de_CH': 'nachbefragung-codebuch-de.pdf',
            'fr_CH': 'nachbefragung-codebuch-fr.pdf',
        }
    )
    post_vote_poll_codebook_xlsx = LocalizedFile(
        label=_('Codebook for the post-vote poll'),
        extension='xlsx',
        static_views={
            'de_CH': 'nachbefragung-codebuch-de.xlsx',
            'fr_CH': 'nachbefragung-codebuch-fr.xlsx',
        }
    )
    post_vote_poll_report = LocalizedFile(
        label=_('Technical report of the post-vote poll'),
        extension='pdf',
        static_views={
            'de_CH': 'nachbefragung-technischer-bericht.pdf',
        }
    )
    preliminary_examination = LocalizedFile(
        label=_('Preliminary examination'),
        extension='pdf',
        static_views={
            'de_CH': 'vorpruefung-de.pdf',
            'fr_CH': 'vorpruefung-fr.pdf',
        }
    )

    campaign_material_yea = FileSubCollection()
    campaign_material_nay = FileSubCollection()

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
        'realization',
        'preliminary_examination'
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

    def get_file(self, name, locale=None, fallback=True):
        """ Returns the requested localized file.

        Uses the current locale if no locale is given.

        Falls back to the default locale if the file is not available in the
        requested locale.

        """
        get = SwissVote.__dict__.get(name).__get_by_locale__
        default_locale = self.session_manager.default_locale
        fallback = get(self, default_locale) if fallback else None
        result = get(self, locale) if locale else getattr(self, name, None)
        return result or fallback
