from __future__ import annotations

from collections import OrderedDict
from functools import cached_property
from onegov.core.orm import observes
from onegov.core.orm import Base
from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON
from onegov.file.utils import word_count
from onegov.pdf.utils import extract_pdf_info
from onegov.swissvotes import _
from onegov.swissvotes.models.actor import Actor
from onegov.swissvotes.models.file import FileSubCollection
from onegov.swissvotes.models.file import LocalizedFile
from onegov.swissvotes.models.file import LocalizedFiles
from onegov.swissvotes.models.file import SwissVoteFile
from onegov.swissvotes.models.policy_area import PolicyArea
from onegov.swissvotes.models.region import Region
from operator import itemgetter
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
from typing import Generic
from typing import NamedTuple
from typing import TYPE_CHECKING
from typing_extensions import TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import date as date_t
    from decimal import Decimal
    from onegov.core.orm import SessionManager
    from onegov.swissvotes.request import SwissvotesRequest
    from typing import Protocol

    T = TypeVar('T')

    class HasCodes(Protocol[T]):
        def codes(self, attribute: str, /) -> dict[int | None, T]: ...

    class HasSessionManager(Protocol):
        @property
        def session_manager(self) -> SessionManager | None: ...

StrT = TypeVar('StrT', bound=str | None, default=str | None)


class Poster(NamedTuple):
    thumbnail: str
    image: str
    url: str | None
    label: str


class encoded_property:  # noqa: N801
    """ A shorthand property to return the label of an encoded value. Requires
    the instance the have a `codes`-lookup function. Creates the SqlAlchemy
    Column (with a prefixed underline).

    Example:

        class MyClass:
            value = encoded_property()

            def codes(self, attributes):
                return {0: 'None', 1: 'One'}

    """

    def __init__(self, nullable: bool = True):
        self.nullable = nullable

    def __set_name__(self, owner: type[HasCodes[T]], name: str) -> None:
        self.name = name
        assert not hasattr(owner, f'_{name}')
        setattr(
            owner, f'_{name}', Column(name, Integer, nullable=self.nullable)
        )

    def __get__(
            self,
            instance: HasCodes[T],
            owner: type[object]
    ) -> T | None:
        value = getattr(instance, f'_{self.name}')
        return instance.codes(self.name).get(value)


class localized_property(Generic[StrT]):  # noqa: N801
    """ A shorthand property to return a localized attribute. Requires at least
    a `xxx_de` attribute and falls back to this.

    Example:

        class MyClass:
            value_de = Column(Text)
            value_fr = Column(Text)
            value = localized_property()
    """

    def __set_name__(
            self,
            owner: type[HasSessionManager],
            name: str
    ) -> None:
        self.name = name

    def __get__(
            self,
            instance: HasSessionManager,
            owner: type[HasSessionManager]
    ) -> StrT:
        default: StrT = getattr(instance, f'{self.name}_de')
        assert instance.session_manager is not None
        assert instance.session_manager.current_locale is not None
        lang = instance.session_manager.current_locale[:2]
        attribute = f'{self.name}_{lang}'
        return getattr(instance, attribute, default) or default


class SwissVote(Base, TimestampMixin, LocalizedFiles, ContentMixin):
    """ A single vote as defined by the code book.

    There are a lot of columns:

    * Some general, ready to be used attributes (bfs_number, ...)
    * Encoded attributes, where the raw integer value is stored prefixed with
      an underline and the attribute returns a translatable label by using the
      ``codes`` function, e.g.  ``_legal_form``, ``legal_form`` and
      ``codes(' _legal_form')``.
    * Descriptors, easily accessible by using ``policy_areas``.
    * A lot of lazy loaded, cantonal results only used when importing/exporting
      the dataset.
    * Recommendations from different parties and assocciations. Internally
      stored as JSON and easily accessible and group by slogan with
      ``recommendations_parties``, ``recommendations_divergent_parties`` and
      ``recommendations_associations``.
    * Different localized attachments, some of them indexed for full text
      search.

    * Metadata from external information sources such as Museum für Gestaltung
      can be stored in the content or meta field provided by the
      ``ContentMixin``.

    """

    __tablename__ = 'swissvotes'

    ORGANIZATION_NO_LONGER_EXISTS = 9999

    term: str | None = None

    if TYPE_CHECKING:
        # we declare the internal numeric coded attributes
        # so mypy knows about them
        _legal_form: Column[int]
        _parliamentary_initiated: Column[int | None]
        _result: Column[int]
        _result_people_accepted: Column[int]
        _result_cantons_accepted: Column[int]
        _result_ag_accepted: Column[int | None]
        _result_ai_accepted: Column[int | None]
        _result_ar_accepted: Column[int | None]
        _result_be_accepted: Column[int | None]
        _result_bl_accepted: Column[int | None]
        _result_bs_accepted: Column[int | None]
        _result_fr_accepted: Column[int | None]
        _result_ge_accepted: Column[int | None]
        _result_gl_accepted: Column[int | None]
        _result_gr_accepted: Column[int | None]
        _result_ju_accepted: Column[int | None]
        _result_lu_accepted: Column[int | None]
        _result_ne_accepted: Column[int | None]
        _result_nw_accepted: Column[int | None]
        _result_ow_accepted: Column[int | None]
        _result_sg_accepted: Column[int | None]
        _result_sh_accepted: Column[int | None]
        _result_so_accepted: Column[int | None]
        _result_sz_accepted: Column[int | None]
        _result_tg_accepted: Column[int | None]
        _result_ti_accepted: Column[int | None]
        _result_ur_accepted: Column[int | None]
        _result_vd_accepted: Column[int | None]
        _result_vs_accepted: Column[int | None]
        _result_zg_accepted: Column[int | None]
        _result_zh_accepted: Column[int | None]
        _position_council_of_states: Column[int]
        _position_federal_council: Column[int]
        _position_national_council: Column[int]
        _position_parliament: Column[int]
        _recommendation: Column[int | None]

    @staticmethod
    def codes(attribute: str) -> dict[int | None, str]:
        """ Returns the codes for the given attribute as defined in the code
        book.

        """

        if attribute == 'legal_form':
            return OrderedDict((
                (1, _('Mandatory referendum')),
                (2, _('Optional referendum')),
                (3, _('Popular initiative')),
                (4, _('Direct counter-proposal')),
                (5, _('Tie-breaker')),
            ))

        if attribute == 'parliamentary_initiated':
            return OrderedDict((
                (0, _('No')),
                (1, _('Yes')),
                (None, _('No')),
            ))

        if attribute == 'result' or attribute.endswith('_accepted'):
            return OrderedDict((
                (0, _('Rejected')),
                (1, _('Accepted')),
                (3, _('Majority of the cantons not necessary')),
                (8, _('Counter-proposal preferred')),
                (9, _('Popular initiative preferred')),
            ))

        if attribute in (
                'position_council_of_states',
                'position_federal_council',
                'position_national_council',
                'position_parliament',
        ):
            return OrderedDict((
                (1, _('Accepting')),
                (2, _('Rejecting')),
                (3, _('None')),
                (8, _('Preference for the counter-proposal')),
                (9, _('Preference for the popular initiative')),
            ))

        if attribute == 'recommendation':
            # Sorted by how it should be displayed in strengths table
            return OrderedDict((
                (1, _('Yea')),
                (9, _('Preference for the popular initiative')),
                (2, _('Nay')),
                (8, _('Preference for the counter-proposal')),
                (4, _('Empty')),
                (5, _('Free vote')),
                (3, _('None')),
                (66, _('Neutral')),
                (9999, _('Organization no longer exists')),
                (None, _('unknown'))
            ))

        raise RuntimeError(f"No codes available for '{attribute}'")

    @staticmethod
    def metadata_codes(attribute: str) -> dict[str, str]:
        if attribute == 'position':
            return OrderedDict((
                ('yes', _('Yes')),
                ('mixed', _('Mixed')),
                ('no', _('No')),
                ('neutral', _('Neutral')),
            ))

        if attribute == 'language':
            return OrderedDict((
                ('de', _('German')),
                ('fr', _('French')),
                ('it', _('Italian')),
                ('rm', _('Rhaeto-Romanic')),
                ('en', _('English')),
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

    id: Column[int] = Column(Integer, nullable=False, primary_key=True)

    # Formal description
    bfs_number: Column[Decimal] = Column(Numeric(8, 2), nullable=False)
    date: Column[date_t] = Column(Date, nullable=False)
    title_de: Column[str] = Column(Text, nullable=False)
    title_fr: Column[str] = Column(Text, nullable=False)
    title: localized_property[str] = localized_property()
    short_title_de: Column[str] = Column(Text, nullable=False)
    short_title_fr: Column[str] = Column(Text, nullable=False)
    short_title_en: Column[str | None] = Column(Text, nullable=True)
    short_title: localized_property[str] = localized_property()
    brief_description_title: Column[str | None] = Column(Text)
    keyword: Column[str | None] = Column(Text)
    legal_form = encoded_property(nullable=False)
    parliamentary_initiated = encoded_property()
    initiator_de: Column[str | None] = Column(Text)
    initiator_fr: Column[str | None] = Column(Text)
    initiator = localized_property()
    anneepolitique: Column[str | None] = Column(Text)
    bfs_map_de: Column[str | None] = Column(Text)
    bfs_map_fr: Column[str | None] = Column(Text)
    bfs_map_en: Column[str | None] = Column(Text)
    bfs_map = localized_property()
    bfs_dashboard_de: Column[str | None] = Column(Text)
    bfs_dashboard_fr: Column[str | None] = Column(Text)
    bfs_dashboard_en: Column[str | None] = Column(Text)
    bfs_dashboard = localized_property()

    @property
    def bfs_map_host(self) -> str | None:
        """ Returns the Host of the BFS Map link for CSP. """

        if self.bfs_map is None:
            return None

        try:
            return urlunparse(list(urlparse(self.bfs_map)[:2]) + 4 * [''])
        except ValueError:
            return None

    # Additional links
    link_curia_vista_de: dict_property[str | None] = content_property()
    link_curia_vista_fr: dict_property[str | None] = content_property()
    link_curia_vista = localized_property()
    link_bk_results_de: dict_property[str | None] = content_property()
    link_bk_results_fr: dict_property[str | None] = content_property()
    link_bk_results = localized_property()
    link_bk_chrono_de: dict_property[str | None] = content_property()
    link_bk_chrono_fr: dict_property[str | None] = content_property()
    link_bk_chrono = localized_property()
    link_federal_council_de: dict_property[str | None] = content_property()
    link_federal_council_fr: dict_property[str | None] = content_property()
    link_federal_council_en: dict_property[str | None] = content_property()
    link_federal_council = localized_property()
    link_federal_departement_de: dict_property[str | None] = content_property()
    link_federal_departement_fr: dict_property[str | None] = content_property()
    link_federal_departement_en: dict_property[str | None] = content_property()
    link_federal_departement = localized_property()
    link_federal_office_de: dict_property[str | None] = content_property()
    link_federal_office_fr: dict_property[str | None] = content_property()
    link_federal_office_en: dict_property[str | None] = content_property()
    link_federal_office = localized_property()
    link_post_vote_poll_de: dict_property[str | None] = content_property()
    link_post_vote_poll_fr: dict_property[str | None] = content_property()
    link_post_vote_poll_en: dict_property[str | None] = content_property()
    link_post_vote_poll = localized_property()
    link_easyvote_de: dict_property[str | None] = content_property()
    link_easyvote_fr: dict_property[str | None] = content_property()
    link_easyvote = localized_property()
    link_campaign_yes_1_de: dict_property[str | None] = content_property()
    link_campaign_yes_1_fr: dict_property[str | None] = content_property()
    link_campaign_yes_1 = localized_property()
    link_campaign_yes_2_de: dict_property[str | None] = content_property()
    link_campaign_yes_2_fr: dict_property[str | None] = content_property()
    link_campaign_yes_2 = localized_property()
    link_campaign_yes_3_de: dict_property[str | None] = content_property()
    link_campaign_yes_3_fr: dict_property[str | None] = content_property()
    link_campaign_yes_3 = localized_property()
    link_campaign_no_1_de: dict_property[str | None] = content_property()
    link_campaign_no_1_fr: dict_property[str | None] = content_property()
    link_campaign_no_1 = localized_property()
    link_campaign_no_2_de: dict_property[str | None] = content_property()
    link_campaign_no_2_fr: dict_property[str | None] = content_property()
    link_campaign_no_2 = localized_property()
    link_campaign_no_3_de: dict_property[str | None] = content_property()
    link_campaign_no_3_fr: dict_property[str | None] = content_property()
    link_campaign_no_3 = localized_property()

    @cached_property
    def campaign_links(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for position, label in (
                ('yes', _('Campaign for a Yes')),
                ('no', _('Campaign for a No'))
        ):
            for number in (1, 2, 3):
                link = getattr(self, f'link_campaign_{position}_{number}', '')
                if link:
                    result.setdefault(label, []).append(link)
        return result

    # Campaign finances
    campaign_finances_yea_total: Column[int | None] = Column(Integer())
    campaign_finances_nay_total: Column[int | None] = Column(Integer())
    campaign_finances_yea_donors_de: dict_property[str | None] = (
        content_property()
    )
    campaign_finances_yea_donors_fr: dict_property[str | None] = (
        content_property()
    )
    campaign_finances_yea_donors = localized_property()
    campaign_finances_nay_donors_de: dict_property[str | None] = (
        content_property()
    )
    campaign_finances_nay_donors_fr: dict_property[str | None] = (
        content_property()
    )
    campaign_finances_nay_donors = localized_property()
    campaign_finances_link_de: dict_property[str | None] = content_property()
    campaign_finances_link_fr: dict_property[str | None] = content_property()
    campaign_finances_link = localized_property()

    # space-separated poster URLs coming from the dataset
    posters_mfg_yea: Column[str | None] = Column(Text)
    posters_mfg_nay: Column[str | None] = Column(Text)
    posters_bs_yea: Column[str | None] = Column(Text)
    posters_bs_nay: Column[str | None] = Column(Text)
    posters_sa_yea: Column[str | None] = Column(Text)
    posters_sa_nay: Column[str | None] = Column(Text)

    # Fetched list of image urls using MfG API
    posters_mfg_yea_imgs: dict_property[dict[str, Any]] = content_property(
        default=dict
    )
    posters_mfg_nay_imgs: dict_property[dict[str, Any]] = content_property(
        default=dict
    )

    # Fetched list of image urls using bs API
    posters_bs_yea_imgs: dict_property[dict[str, Any]] = content_property(
        default=dict
    )
    posters_bs_nay_imgs: dict_property[dict[str, Any]] = content_property(
        default=dict
    )

    # Fetched list of image urls using SA API
    posters_sa_yea_imgs: dict_property[dict[str, Any]] = content_property(
        default=dict
    )
    posters_sa_nay_imgs: dict_property[dict[str, Any]] = content_property(
        default=dict
    )

    def posters(self, request: SwissvotesRequest) -> dict[str, list[Poster]]:
        result: dict[str, list[Poster]] = {'yea': [], 'nay': []}

        # order: MfG, SA, BS
        for key, attribute, label in (
                ('yea', 'posters_mfg_yea', _('Link eMuseum.ch')),
                ('nay', 'posters_mfg_nay', _('Link eMuseum.ch')),
                ('yea', 'posters_sa_yea', _('Link Social Archives')),
                ('nay', 'posters_sa_nay', _('Link Social Archives')),
                ('yea', 'posters_bs_yea', _('Link Basel Poster Collection')),
                ('nay', 'posters_bs_nay', _('Link Basel Poster Collection')),
        ):
            images = getattr(self, f'{attribute}_imgs')
            urls = (getattr(self, attribute) or '').strip().split(' ')
            for url in urls:
                image = images.get(url)
                if image:
                    result[key].append(
                        Poster(
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
                    Poster(
                        thumbnail=request.link(image, 'thumbnail'),
                        image=request.link(image),
                        url=None,
                        label=label
                    )
                )

        return result

    # Media
    media_ads_total: Column[int | None] = Column(Integer)
    media_ads_yea_p: Column[Decimal | None] = Column(Numeric(13, 10))
    media_coverage_articles_total: Column[int | None] = Column(Integer)
    media_coverage_tonality_total: Column[Decimal | None] = Column(
        Numeric(13, 10)
    )

    # Descriptor
    descriptor_1_level_1: Column[Decimal | None] = Column(Numeric(8, 4))
    descriptor_1_level_2: Column[Decimal | None] = Column(Numeric(8, 4))
    descriptor_1_level_3: Column[Decimal | None] = Column(Numeric(8, 4))
    descriptor_2_level_1: Column[Decimal | None] = Column(Numeric(8, 4))
    descriptor_2_level_2: Column[Decimal | None] = Column(Numeric(8, 4))
    descriptor_2_level_3: Column[Decimal | None] = Column(Numeric(8, 4))
    descriptor_3_level_1: Column[Decimal | None] = Column(Numeric(8, 4))
    descriptor_3_level_2: Column[Decimal | None] = Column(Numeric(8, 4))
    descriptor_3_level_3: Column[Decimal | None] = Column(Numeric(8, 4))

    @cached_property
    def policy_areas(self) -> list[PolicyArea]:
        """ Returns the policy areas / descriptors of the vote. """

        def get_level(number: int, level: int) -> PolicyArea | None:
            value = getattr(self, f'descriptor_{number}_level_{level}')
            if value is None:
                return None
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
    result_turnout: Column[Decimal | None] = Column(Numeric(13, 10))
    result_people_accepted = encoded_property()
    result_people_yeas_p: Column[Decimal | None] = Column(Numeric(13, 10))
    result_cantons_accepted = encoded_property()
    result_cantons_yeas: Column[Decimal | None] = Column(Numeric(3, 1))
    result_cantons_nays: Column[Decimal | None] = Column(Numeric(3, 1))
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
    def number_of_cantons(self) -> int:
        if self.bfs_number <= 292:
            return 22
        return 23

    @cached_property
    def results_cantons(self) -> dict[str, list[Region]]:
        """ Returns the results of all cantons. """

        result: dict[int, list[Region]] = {}
        value: int | None
        for canton in Region.cantons():
            value = getattr(self, f'_result_{canton}_accepted')
            if value is not None:
                result.setdefault(value, []).append(Region(canton))

        codes = self.codes('result_accepted')
        return OrderedDict(
            (codes[key], regions)
            for key, regions in sorted(result.items(), key=itemgetter(0))
        )

    # Authorities
    procedure_number: Column[str | None] = Column(Text)
    position_federal_council = encoded_property()
    position_parliament = encoded_property()
    position_national_council = encoded_property()
    position_national_council_yeas: Column[int | None] = Column(Integer)
    position_national_council_nays: Column[int | None] = Column(Integer)
    position_council_of_states = encoded_property()
    position_council_of_states_yeas: Column[int | None] = Column(Integer)
    position_council_of_states_nays: Column[int | None] = Column(Integer)

    # Duration
    duration_federal_assembly: Column[int | None] = Column(Integer)
    duration_initative_collection: Column[int | None] = Column(Integer)
    duration_referendum_collection: Column[int | None] = Column(Integer)
    signatures_valid: Column[int | None] = Column(Integer)

    # Voting recommendations
    recommendations: Column[dict[str, int | None]] = Column(
        JSON,
        nullable=False,
        default=dict
    )
    recommendations_other_yes_de: Column[str | None] = Column(Text)
    recommendations_other_yes_fr: Column[str | None] = Column(Text)
    recommendations_other_yes = localized_property()
    recommendations_other_no_de: Column[str | None] = Column(Text)
    recommendations_other_no_fr: Column[str | None] = Column(Text)
    recommendations_other_no = localized_property()
    recommendations_other_counter_proposal_de: Column[str | None] = (
        Column(Text)
    )
    recommendations_other_counter_proposal_fr: Column[str | None] = (
        Column(Text)
    )
    recommendations_other_counter_proposal = localized_property()
    recommendations_other_popular_initiative_de: Column[str | None] = (
        Column(Text)
    )
    recommendations_other_popular_initiative_fr: Column[str | None] = (
        Column(Text)
    )
    recommendations_other_popular_initiative = localized_property()
    recommendations_other_free_de: Column[str | None] = Column(Text)
    recommendations_other_free_fr: Column[str | None] = Column(Text)
    recommendations_other_free = localized_property()
    recommendations_divergent: Column[dict[str, Any]] = Column(
        JSON,
        nullable=False,
        default=dict
    )

    def get_recommendation(self, name: str) -> str | None:
        """ Get the recommendations by name. """
        return self.codes('recommendation').get(
            self.recommendations.get(name)
        )

    def get_recommendation_of_existing_parties(self) -> dict[str, int | None]:
        """ Get only the existing parties as when this vote was conducted """
        if not self.recommendations:
            return {}
        return {
            k: v for k, v in self.recommendations.items()
            if v != self.ORGANIZATION_NO_LONGER_EXISTS
        }

    def group_recommendations(
            self,
            recommendations: Iterable[tuple[T, int | None]],
            ignore_unknown: bool = False
    ) -> dict[str, list[T]]:
        """ Group the given recommendations by slogan. """

        codes = self.codes('recommendation')
        recommendation_codes = list(codes.keys())

        def by_recommendation(reco: tuple[int | None, list[T]]) -> int:
            return recommendation_codes.index(reco[0])

        result: dict[int | None, list[T]] = {}
        for actor, recommendation in recommendations:
            if recommendation == self.ORGANIZATION_NO_LONGER_EXISTS:
                continue
            if ignore_unknown and recommendation is None:
                continue

            result.setdefault(recommendation, []).append(actor)

        return OrderedDict(
            (codes[key], actors)
            for key, actors in sorted(result.items(), key=by_recommendation)
        )

    def get_actors_share(self, actor: str) -> int:
        assert isinstance(actor, str), 'Actor must be a string'
        attr = f'national_council_share_{actor}'
        return getattr(self, attr, 0) or 0

    @cached_property
    def sorted_actors_list(self) -> list[str]:
        """
         Returns a list of actors of the current vote sorted by:

        1. codes for recommendations (strength table)
        2. by electoral share (descending)

        It filters out those parties who have no electoral share

        """
        result = []
        for actor_list in self.recommendations_parties.values():
            actors = (d.name for d in actor_list)
            result.extend(
                sorted(actors, key=self.get_actors_share, reverse=True)
            )
        return result

    @cached_property
    def recommendations_parties(self) -> dict[str, list[Actor]]:
        """ The recommendations of the parties grouped by slogans. """

        recommendations = self.recommendations or {}
        return self.group_recommendations((
            (Actor(name), recommendations.get(name))
            for name in Actor.parties()
        ), ignore_unknown=True)

    @cached_property
    def recommendations_divergent_parties(
            self
    ) -> dict[str, list[tuple[Actor, Region]]]:
        """ The divergent recommendations of the parties grouped by slogans.

        """

        recommendations = self.recommendations_divergent or {}
        return self.group_recommendations((
            (
                (Actor(name.split('_')[0]), Region(name.split('_')[1])),
                recommendation,
            )
            for name, recommendation in sorted(recommendations.items())
        ), ignore_unknown=True)

    @cached_property
    def recommendations_associations(self) -> dict[str, list[Actor]]:
        """ The recommendations of the associations grouped by slogans. """
        recommendations_lookup = self.recommendations or {}
        recommendations = [
            (Actor(name), recommendations_lookup.get(name))
            for name in Actor.associations()
        ]
        recommendations.extend(
            (Actor(stripped), code)
            for attribute, code in (
                ('yes', 1),
                ('no', 2),
                ('free', 5),
                ('counter_proposal', 8),
                ('popular_initiative', 9),
            )
            if (value := getattr(self, f'recommendations_other_{attribute}'))
            for name in value.split(',')
            if (stripped := name.strip())
        )

        return self.group_recommendations(recommendations, ignore_unknown=True)

    # Electoral strength
    national_council_election_year: Column[int | None] = Column(Integer)
    national_council_share_fdp: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_cvp: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_sps: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_svp: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_lps: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_ldu: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_evp: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_csp: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_pda: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_poch: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_gps: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_sd: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_rep: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_edu: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_fps: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_lega: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_kvp: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_glp: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_bdp: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_mcg: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_mitte: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_ubrige: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_yeas: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_nays: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_none: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_empty: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_free_vote: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_neutral: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )
    national_council_share_unknown: Column[Decimal | None] = (
        Column(Numeric(13, 10))
    )

    @cached_property
    def has_national_council_share_data(self) -> bool:
        """ Returns true, if the vote contains national council share data.

        Returns true, if a national council year is set and

        * any aggregated national council share data is present (yeas, nays,
            none, empty, free vote, neutral, unknown)
        * or any national council share data of parties with national council
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
    files = associated(SwissVoteFile, 'files', 'one-to-many')
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
        label=_('Full analysis of VOX post-vote poll results'),
        extension='pdf',
        static_views={
            'de_CH': 'nachbefragung-de.pdf',
            'fr_CH': 'nachbefragung-fr.pdf',
        }
    )
    post_vote_poll_methodology = LocalizedFile(
        label=_('Questionnaire of the VOX poll'),
        extension='pdf',
        static_views={
            'de_CH': 'nachbefragung-methode-de.pdf',
            'fr_CH': 'nachbefragung-methode-fr.pdf',
        }
    )
    post_vote_poll_dataset = LocalizedFile(
        label=_('Dataset of the VOX poll'),
        extension='csv',
        static_views={
            'de_CH': 'nachbefragung.csv',
        }
    )
    post_vote_poll_dataset_sav = LocalizedFile(
        label=_('Dataset of the VOX poll'),
        extension='sav',
        static_views={
            'de_CH': 'nachbefragung.sav',
        }
    )
    post_vote_poll_dataset_dta = LocalizedFile(
        label=_('Dataset of the VOX poll'),
        extension='dta',
        static_views={
            'de_CH': 'nachbefragung.dta',
        }
    )
    post_vote_poll_codebook = LocalizedFile(
        label=_('Codebook for the VOX poll'),
        extension='pdf',
        static_views={
            'de_CH': 'nachbefragung-codebuch-de.pdf',
            'fr_CH': 'nachbefragung-codebuch-fr.pdf',
        }
    )
    post_vote_poll_codebook_xlsx = LocalizedFile(
        label=_('Codebook for the VOX poll'),
        extension='xlsx',
        static_views={
            'de_CH': 'nachbefragung-codebuch-de.xlsx',
            'fr_CH': 'nachbefragung-codebuch-fr.xlsx',
        }
    )
    post_vote_poll_report = LocalizedFile(
        label=_('Technical report on the VOX poll'),
        extension='pdf',
        static_views={
            'de_CH': 'nachbefragung-technischer-bericht.pdf',
        }
    )
    leewas_post_vote_poll_results = LocalizedFile(
        label=_('Results of the LeeWas post-vote poll'),
        extension='pdf',
        static_views={
            'de_CH': 'ergebnisse-der-leewas-nachbefragung.pdf',
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
    campaign_finances_xlsx = LocalizedFile(
        label=_('Campaign finances'),
        extension='xlsx',
        static_views={
            'de_CH': 'kampagnenfinanzierung-de.xlsx',
            'fr_CH': 'kampagnenfinanzierung-fr.xlsx',
        }
    )

    campaign_material_yea = FileSubCollection()
    campaign_material_nay = FileSubCollection()
    campaign_material_other = FileSubCollection()
    campaign_material_metadata: Column[dict[str, Any]] = Column(
        JSON,
        nullable=False,
        default=dict
    )

    # searchable attachment texts
    searchable_text_de_CH = deferred(Column(TSVECTOR))  # noqa: N815
    searchable_text_fr_CH = deferred(Column(TSVECTOR))  # noqa: N815
    searchable_text_it_CH = deferred(Column(TSVECTOR))  # noqa: N815
    searchable_text_en_US = deferred(Column(TSVECTOR))  # noqa: N815

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

    def reindex_files(self) -> None:
        """ Extract the text from the localized files and the campaign
        material and save it together with the language. Store the text of the
        **indexed only** localized files and **all** campaign material
        in the search indexes.

        The language is determined as follows:

        * For the localized files, the language is determined by the locale,
          e.g. `de_CH` -> `german`.
        * For the campaign material, the campaign metadata is used. If a
          document is (amongst others) `de` --> `german`. If (amongst others,)
          `fr` but not `de` --> `french`. If (amongst others) `it` but not `de`
          or `fr` --> `italian`. In all other cases `english`.

        """

        file: SwissVoteFile | None
        locales = {
            'de_CH': 'german',
            'fr_CH': 'french',
            'it_CH': 'italian',
            'en_US': 'english'
        }
        files: dict[str, list[tuple[SwissVoteFile, bool]]]
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
    def files_observer(self, files: list[SwissVoteFile]) -> None:
        self.reindex_files()

    def get_file(
            self,
            name: str,
            locale: str | None = None,
            fallback: bool = True
    ) -> SwissVoteFile | None:
        """ Returns the requested localized file.

        Uses the current locale if no locale is given.

        Falls back to the default locale if the file is not available in the
        requested locale.

        """
        get = SwissVote.__dict__[name].__get_by_locale__
        assert self.session_manager is not None
        default_locale = self.session_manager.default_locale
        fallback_file = get(self, default_locale) if fallback else None
        result = get(self, locale) if locale else getattr(self, name, None)
        return result or fallback_file

    @staticmethod
    def search_term_expression(term: str | None) -> str:
        """ Returns the given search term transformed to use within Postgres
        ``to_tsquery`` function.

        Removes all unwanted characters, replaces prefix matching, joins
        word together using FOLLOWED BY.
        """

        def cleanup(text: str) -> str:
            wildcard = text.endswith('*')
            result = ''.join(c for c in text if c.isalnum() or c in ',.')
            if not result:
                return result
            if wildcard:
                return f'{result}:*'
            return result

        return ' <-> '.join(
            cleaned_part
            for part in (term or '').strip().split()
            if (cleaned_part := cleanup(part))
        )

    def search(self, term: str | None = None) -> list[SwissVoteFile]:
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
            or_(*(
                and_(
                    SwissVoteFile.id.in_([file.id for file in self.files]),
                    SwissVoteFile.language == language,
                    func.to_tsvector(language, SwissVoteFile.extract).op('@@')(
                        func.to_tsquery(language, term)
                    )
                )
                for language in ('german', 'french', 'italian', 'english')
            ))
        )
        return query.all()
