from collections import OrderedDict
from functools import cached_property
from onegov.core.orm import observes
from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON
from onegov.core.utils import Bunch
from onegov.file.utils import word_count
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
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import deferred
from urllib.parse import urlparse
from urllib.parse import urlunparse


from typing import Any


class encoded_property:
    """ A shorthand property to return the label of an encoded value. Requires
    the instance the have a `codes`-lookup function. Creates the SqlAlchemy
    Column (with a prefixed underline).

    Example:

        class MyClass:
            value = encoded_property()

            def codes(self, attributes):
                return {0: 'None', 1: 'One'}

    """

    def __init__(self, nullable=True):
        self.nullable = nullable

    def __set_name__(self, owner, name):
        self.name = name
        assert not hasattr(owner, f'_{name}')
        setattr(
            owner, f'_{name}', Column(name, Integer, nullable=self.nullable)
        )

    def __get__(self, instance, owner):
        value = getattr(instance, f'_{self.name}')
        return instance.codes(self.name).get(value)


class localized_property:
    """ A shorthand property to return a localized attribute. Requires at least
    a `xxx_de` attribute and falls back to this.

    Example:

        class MyClass:
            value_de = Column(Text)
            value_fr = Column(Text)
            value = localized_property()
    """
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        default = getattr(instance, f'{self.name}_de', None)
        lang = instance.session_manager.current_locale[:2]
        attribute = f'{self.name}_{lang}'
        if hasattr(instance, attribute):
            return getattr(instance, attribute) or default
        return default


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

    term = None

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
                (5, _("Tie-breaker")),
            ))

        if attribute == 'parliamentary_initiated':
            return OrderedDict((
                (0, _("No")),
                (1, _("Yes")),
                (None, _("No")),
            ))

        if attribute == 'result' or attribute.endswith('_accepted'):
            return OrderedDict((
                (0, _("Rejected")),
                (1, _("Accepted")),
                (3, _("Majority of the cantons not necessary")),
                (8, _("Counter-proposal preferred")),
                (9, _("Popular initiative preferred")),
            ))

        if attribute in (
            'position_council_of_states',
            'position_federal_council',
            'position_national_council',
            'position_parliament',
        ):
            return OrderedDict((
                (1, _("Accepting")),
                (2, _("Rejecting")),
                (3, _("None")),
                (8, _("Preference for the counter-proposal")),
                (9, _("Preference for the popular initiative")),
            ))

        if attribute == 'recommendation':
            # Sorted by how it should be displayed in strengths table
            return OrderedDict((
                (1, _("Yea")),
                (9, _("Preference for the popular initiative")),
                (2, _("Nay")),
                (8, _("Preference for the counter-proposal")),
                (4, _("Empty")),
                (5, _("Free vote")),
                (3, _("None")),
                (66, _("Neutral")),
                (9999, _("Organization no longer exists")),
                (None, _("unknown"))
            ))

    @staticmethod
    def metadata_codes(attribute):
        if attribute == 'position':
            return OrderedDict((
                ('yes', _("Yes")),
                ('mixed', _("Mixed")),
                ('no', _("No")),
                ('neutral', _("Neutral")),
            ))

        if attribute == 'language':
            return OrderedDict((
                ('de', _('German')),
                ('fr', _('French')),
                ('it', _('Italian')),
                ('rm', _('Rhaeto-Romanic')),
                ('mixed', _('Mixed')),
                ('other', _('Other')),
            ))

        if attribute == 'doctype':
            return OrderedDict((
                ('argument', _('Collection of arguments')),
                ('letter', _('Letter')),
                ('documentation', _('Documentation')),
                ('leaflet', _('Pamphlet')),
                ('release', _('Media release')),
                ('memberships', _('List of members')),
                ('article', _('Press article')),
                ('legal', _('Legal text')),
                ('lecture', _('Text of a presentation')),
                ('statistics', _('Statistical data')),
                ('other', _('Other')),
                ('website', _('Website')),
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
    short_title_en = Column(Text, nullable=True)
    short_title = localized_property()
    brief_description_title = Column(Text)
    keyword = Column(Text)
    legal_form = encoded_property(nullable=False)
    parliamentary_initiated = encoded_property()
    initiator_de = Column(Text)
    initiator_fr = Column(Text)
    initiator = localized_property()
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

    # Additional links
    link_curia_vista_de = content_property()
    link_curia_vista_fr = content_property()
    link_curia_vista = localized_property()
    link_bk_results_de = content_property()
    link_bk_results_fr = content_property()
    link_bk_results = localized_property()
    link_bk_chrono_de = content_property()
    link_bk_chrono_fr = content_property()
    link_bk_chrono = localized_property()
    link_federal_council_de = content_property()
    link_federal_council_fr = content_property()
    link_federal_council_en = content_property()
    link_federal_council = localized_property()
    link_federal_departement_de = content_property()
    link_federal_departement_fr = content_property()
    link_federal_departement_en = content_property()
    link_federal_departement = localized_property()
    link_federal_office_de = content_property()
    link_federal_office_fr = content_property()
    link_federal_office_en = content_property()
    link_federal_office = localized_property()
    link_post_vote_poll_de = content_property()
    link_post_vote_poll_fr = content_property()
    link_post_vote_poll_en = content_property()
    link_post_vote_poll = localized_property()
    link_easyvote_de = content_property()
    link_easyvote_fr = content_property()
    link_easyvote = localized_property()
    link_campaign_yes_1_de = content_property()
    link_campaign_yes_1_fr = content_property()
    link_campaign_yes_1 = localized_property()
    link_campaign_yes_2_de = content_property()
    link_campaign_yes_2_fr = content_property()
    link_campaign_yes_2 = localized_property()
    link_campaign_yes_3_de = content_property()
    link_campaign_yes_3_fr = content_property()
    link_campaign_yes_3 = localized_property()
    link_campaign_no_1_de = content_property()
    link_campaign_no_1_fr = content_property()
    link_campaign_no_1 = localized_property()
    link_campaign_no_2_de = content_property()
    link_campaign_no_2_fr = content_property()
    link_campaign_no_2 = localized_property()
    link_campaign_no_3_de = content_property()
    link_campaign_no_3_fr = content_property()
    link_campaign_no_3 = localized_property()

    @cached_property
    def campaign_links(self):
        result = {}
        for position, label in (
            ('yes', _('Campaign for a Yes')),
            ('no', _('Campaign for a No'))
        ):
            for number in (1, 2, 3):
                link = getattr(self, f'link_campaign_{position}_{number}', '')
                if link:
                    result.setdefault(label, [])
                    result[label].append(link)
        return result

    # space-separated poster URLs coming from the dataset
    posters_mfg_yea = Column(Text)
    posters_mfg_nay = Column(Text)
    posters_sa_yea = Column(Text)
    posters_sa_nay = Column(Text)

    # Fetched list of image urls using MfG API
    posters_mfg_yea_imgs: dict_property[dict[str, Any]] = content_property(
        default=dict
    )
    posters_mfg_nay_imgs: dict_property[dict[str, Any]] = content_property(
        default=dict
    )

    # Fetched list of image urls using SA API
    posters_sa_yea_imgs: dict_property[dict[str, Any]] = content_property(
        default=dict
    )
    posters_sa_nay_imgs: dict_property[dict[str, Any]] = content_property(
        default=dict
    )

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
    result = encoded_property()
    result_turnout = Column(Numeric(13, 10))
    result_people_accepted = encoded_property()
    result_people_yeas_p = Column(Numeric(13, 10))
    result_cantons_accepted = encoded_property()
    result_cantons_yeas = Column(Numeric(3, 1))
    result_cantons_nays = Column(Numeric(3, 1))
    result_ag_accepted = encoded_property()
    result_ai_accepted = encoded_property()
    result_ar_accepted = encoded_property()
    result_be_accepted = encoded_property()
    result_bl_accepted = encoded_property()
    result_bs_accepted = encoded_property()
    result_fr_accepted = encoded_property()
    result_ge_accepted = encoded_property()
    result_gl_accepted = encoded_property()
    result_gr_accepted = encoded_property()
    result_ju_accepted = encoded_property()
    result_lu_accepted = encoded_property()
    result_ne_accepted = encoded_property()
    result_nw_accepted = encoded_property()
    result_ow_accepted = encoded_property()
    result_sg_accepted = encoded_property()
    result_sh_accepted = encoded_property()
    result_so_accepted = encoded_property()
    result_sz_accepted = encoded_property()
    result_tg_accepted = encoded_property()
    result_ti_accepted = encoded_property()
    result_ur_accepted = encoded_property()
    result_vd_accepted = encoded_property()
    result_vs_accepted = encoded_property()
    result_zg_accepted = encoded_property()
    result_zh_accepted = encoded_property()

    @cached_property
    def number_of_cantons(self):
        if self.bfs_number <= 292:
            return 22
        return 23

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
    procedure_number = Column(Text)
    position_federal_council = encoded_property()
    position_parliament = encoded_property()
    position_national_council = encoded_property()
    position_national_council_yeas = Column(Integer)
    position_national_council_nays = Column(Integer)
    position_council_of_states = encoded_property()
    position_council_of_states_yeas = Column(Integer)
    position_council_of_states_nays = Column(Integer)

    # Duration
    duration_federal_assembly = Column(Integer)
    duration_initative_collection = Column(Integer)
    duration_referendum_collection = Column(Integer)
    signatures_valid = Column(Integer)

    # Voting recommendations
    recommendations = Column(JSON, nullable=False, default=dict)
    recommendations_other_yes_de = Column(Text)
    recommendations_other_yes_fr = Column(Text)
    recommendations_other_yes = localized_property()
    recommendations_other_no_de = Column(Text)
    recommendations_other_no_fr = Column(Text)
    recommendations_other_no = localized_property()
    recommendations_other_counter_proposal_de = Column(Text)
    recommendations_other_counter_proposal_fr = Column(Text)
    recommendations_other_counter_proposal = localized_property()
    recommendations_other_popular_initiative_de = Column(Text)
    recommendations_other_popular_initiative_fr = Column(Text)
    recommendations_other_popular_initiative = localized_property()
    recommendations_other_free_de = Column(Text)
    recommendations_other_free_fr = Column(Text)
    recommendations_other_free = localized_property()
    recommendations_divergent = Column(JSON, nullable=False, default=dict)

    def get_recommendation(self, name):
        """ Get the recommendations by name. """
        return self.codes('recommendation').get(
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

        codes = self.codes('recommendation')
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

    def get_actors_share(self, actor):
        assert isinstance(actor, str), 'Actor must be a string'
        attr = f'national_council_share_{actor}'
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

        def as_list(attribute, code):
            value = getattr(self, f'recommendations_other_{attribute}')
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
        for attribute, code in (
            ('yes', 1),
            ('no', 2),
            ('free', 5),
            ('counter_proposal', 8),
            ('popular_initiative', 9),
        ):
            recommendations.extend(as_list(attribute, code))
        return self.group_recommendations(recommendations, ignore_unknown=True)

    # Electoral strength
    national_council_election_year = Column(Integer)
    national_council_share_fdp = Column(Numeric(13, 10))
    national_council_share_cvp = Column(Numeric(13, 10))
    national_council_share_sps = Column(Numeric(13, 10))
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
        """ Returns true, if the vote contains national council share data.

        Returns true, if a national council year is set and
        - any aggregated national council share data is present (yeas, nays,
          none, empty, free vote, neutral, unknown)
        - or any national council share data of parties with national council
          share and a recommendation regarding this vote is present
        """
        if (
            self.national_council_election_year and (
                self.national_council_share_yeas
                or self.national_council_share_nays
                or self.national_council_share_none
                or self.national_council_share_empty
                or self.national_council_share_free_vote
                or self.national_council_share_neutral
                or self.national_council_share_unknown
                or self.sorted_actors_list
            )
        ):
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
            'de_CH': 'kurzbeschreibung-de.pdf',
            'fr_CH': 'kurzbeschreibung-fr.pdf',
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
    parliamentary_initiative = LocalizedFile(
        label=_('Parliamentary initiative'),
        extension='pdf',
        static_views={
            'de_CH': 'parlamentarische-initiative-de.pdf',
            'fr_CH': 'parlamentarische-initiative-fr.pdf',
        }
    )
    parliamentary_committee_report = LocalizedFile(
        label=_('Report of the parliamentary committee'),
        extension='pdf',
        static_views={
            'de_CH': 'bericht-parlamentarische-kommission-de.pdf',
            'fr_CH': 'bericht-parlamentarische-kommission-fr.pdf',
        }
    )
    federal_council_opinion = LocalizedFile(
        label=_('Opinion of the Federal Council'),
        extension='pdf',
        static_views={
            'de_CH': 'stellungnahme-bundesrat-de.pdf',
            'fr_CH': 'stellungnahme-bundesrat-fr.pdf',
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
    easyvote_booklet = LocalizedFile(
        label=_('Explanatory brochure by easyvote'),
        extension='pdf',
        static_views={
            'de_CH': 'easyvote-de.pdf',
            'fr_CH': 'easyvote-fr.pdf',
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
            'de_CH': 'staatsebenen-de.xlsx',
            'fr_CH': 'staatsebenen-fr.xlsx',
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
    campaign_material_other = FileSubCollection()
    campaign_material_metadata = Column(JSON, nullable=False, default=dict)

    # searchable attachment texts
    searchable_text_de_CH = deferred(Column(TSVECTOR))
    searchable_text_fr_CH = deferred(Column(TSVECTOR))
    searchable_text_it_CH = deferred(Column(TSVECTOR))
    searchable_text_en_US = deferred(Column(TSVECTOR))

    indexed_files = {
        'voting_text',
        'brief_description',
        'federal_council_message',
        'parliamentary_debate',
        # we don't include the voting booklet, resolution, ad analysis and
        # easyvote booklet - they might contain other votes from the same day!
        'realization',
        'preliminary_examination',
    }

    def reindex_files(self):
        """ Extract the text from the localized files and the campaign
        material and save it together with the language. Store the text of the
        **indexed only** localized files and **all** campaign material
        in the search indexes.

        The language is determined as follows:
        - For the localized files, the language is determined by the locale,
          e.g. `de_CH` -> `german`.
        - For the campaign material, the campaign metadata is used. If a
          document is (amongst others) `de` --> `german`. If (amongst others,)
          `fr` but not `de` --> `french`. If (amongst others) `it` but not `de`
          or `fr` --> `italian`. In all other cases `english`.

        """

        locales = {
            'de_CH': 'german',
            'fr_CH': 'french',
            'it_CH': 'italian',
            'en_US': 'english'
        }
        files = {locale: [] for locale in locales}

        # Localized files
        for locale in locales:
            for name, attribute in self.localized_files().items():
                if attribute.extension == 'pdf':
                    file = SwissVote.__dict__[name].__get_by_locale__(
                        self, locale
                    )
                    if file:
                        index = name in self.indexed_files
                        files[locale].append((file, index))

        # Campaign material
        for file in self.campaign_material_other:
            name = file.filename.replace('.pdf', '')
            metadata = (self.campaign_material_metadata or {}).get(name)
            languages = set((metadata or {}).get('language', []))
            if 'de' in languages:
                files['de_CH'].append((file, True))
            elif 'fr' in languages:
                files['fr_CH'].append((file, True))
            elif 'it' in languages:
                files['it_CH'].append((file, True))
            else:
                files['en_US'].append((file, True))

        # Extract content and index
        for locale in files:
            text = ''
            for file, index in files[locale]:
                pages, extract = extract_pdf_info(file.reference.file)
                file.extract = (extract or '').strip()
                file.stats = {
                    'pages': pages,
                    'words': word_count(file.extract)
                }
                file.language = locales[locale]

                if file.extract and index:
                    text += '\n\n' + file.extract

            setattr(
                self,
                f'searchable_text_{locale}',
                func.to_tsvector(locales[locale], text)
            )

    @observes('files', scope='onegov.swissvotes.app.SwissvotesApp')
    def files_observer(self, files):
        self.reindex_files()

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

    @staticmethod
    def search_term_expression(term):
        """ Returns the given search term transformed to use within Postgres
        ``to_tsquery`` function.

        Removes all unwanted characters, replaces prefix matching, joins
        word together using FOLLOWED BY.
        """

        def cleanup(text):
            wildcard = text.endswith('*')
            result = ''.join((c for c in text if c.isalnum() or c in ',.'))
            if not result:
                return result
            if wildcard:
                return f'{result}:*'
            return result

        parts = [cleanup(part) for part in (term or '').strip().split()]
        return ' <-> '.join([part for part in parts if part])

    def search(self, term=None):
        """ Searches for the given term in the indexed attachments.

        Returns a tuple of attribute name and locale which can be used with
        ``get_file``.
        """
        term = self.term if term is None else term
        term = self.search_term_expression(term)
        if not term:
            return []

        from onegov.swissvotes.models.file import SwissVoteFile
        from sqlalchemy.orm import object_session
        from sqlalchemy import func, and_, or_

        query = object_session(self).query(SwissVoteFile)
        query = query.filter(
            or_(*[
                and_(
                    SwissVoteFile.id.in_([file.id for file in self.files]),
                    SwissVoteFile.language == language,
                    func.to_tsvector(language, SwissVoteFile.extract).op('@@')(
                        func.to_tsquery(language, term)
                    )
                )
                for language in ['german', 'french', 'italian', 'english']
            ])
        )
        return query.all()
