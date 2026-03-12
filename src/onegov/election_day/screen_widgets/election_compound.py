from __future__ import annotations

from onegov.election_day import ElectionDayApp
from onegov.election_day.screen_widgets.generic import ChartWidget
from onegov.election_day.screen_widgets.generic import ModelBoundWidget
from onegov.election_day.utils.election_compound import get_elected_candidates
from onegov.election_day.utils.election_compound import get_list_groups
from onegov.election_day.utils.election_compound import get_superregions
from onegov.election_day.utils.parties import get_party_results
from onegov.election_day.utils.parties import get_party_results_deltas
from onegov.election_day.utils.parties import get_party_results_seat_allocation


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.layouts import DefaultLayout
    from onegov.election_day.models import ElectionCompound  # noqa: F401

ElectionCompoundWidget = ModelBoundWidget['ElectionCompound']


@ElectionDayApp.screen_widget(
    tag='election-compound-seat-allocation-table',
    category='election_compound'
)
class ElectionCompoundSeatAllocationTableWidget(ElectionCompoundWidget):
    tag = 'election-compound-seat-allocation-table'
    template = """
        <xsl:template match="election-compound-seat-allocation-table">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['election-compound-seat-allocation-table']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-compound-seat-allocation-table class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        party_years, parties = get_party_results(model)
        seat_allocations = get_party_results_seat_allocation(
            party_years, parties
        )
        return {
            'election_compound': model,
            'party_years': party_years,
            'seat_allocations': seat_allocations,
        }


@ElectionDayApp.screen_widget(
    tag='election-compound-candidates-table',
    category='election_compound'
)
class ElectionCompoundCandidatesTableWidget(ElectionCompoundWidget):
    tag = 'election-compound-candidates-table'
    template = """
        <xsl:template match="election-compound-candidates-table">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['election-compound-candidates-table']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-compound-candidates-table class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        request = layout.request
        session = request.session
        districts = {
            election.id: (
                election.domain_segment,
                layout.request.link(election),
                election.domain_supersegment,
            )
            for election in model.elections
        }
        elected_candidates = get_elected_candidates(model, session).all()
        return {
            'election_compound': model,
            'elected_candidates': elected_candidates,
            'districts': districts,
        }


@ElectionDayApp.screen_widget(
    tag='election-compound-list-groups-table',
    category='election_compound'
)
class ElectionCompoundListGroupsTableWidget(ElectionCompoundWidget):
    tag = 'election-compound-list-groups-table'
    template = """
        <xsl:template match="election-compound-list-groups-table">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['election-compound-list-groups-table']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-compound-list-groups-table class="" />'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        groups = get_list_groups(model)
        return {
            'election': model,
            'groups': groups
        }


@ElectionDayApp.screen_widget(
    tag='election-compound-party-strengths-table',
    category='election_compound'
)
class ElectionCompoundPartyStrengthsTableWidget(ElectionCompoundWidget):
    tag = 'election-compound-party-strengths-table'
    template = """
        <xsl:template match="election-compound-party-strengths-table">
            <div class="{@class}" tal:define="year '{@year}'">
                <tal:block
                    metal:use-macro="layout.macros['party-strengths-table']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-compound-party-strengths-table year="" class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        party_years, parties = get_party_results(model)
        party_deltas, party_results = get_party_results_deltas(
            model, party_years, parties
        )
        return {
            'election': model,
            'party_years': party_years,
            'party_deltas': party_deltas,
            'party_results': party_results
        }


@ElectionDayApp.screen_widget(
    tag='election-compound-districts-table',
    category='election_compound'
)
class ElectionCompoundDistrictsTableWidget(ElectionCompoundWidget):
    tag = 'election-compound-districts-table'
    template = """
        <xsl:template match="election-compound-districts-table">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['election-compound-districts-table']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-compound-districts-table class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'election_compound': model,
        }


@ElectionDayApp.screen_widget(
    tag='election-compound-districts-map',
    category='election_compound'
)
class ElectionCompoundDistrictsMapWidget(ElectionCompoundWidget):
    tag = 'election-compound-districts-map'
    template = """
        <xsl:template match="election-compound-districts-map">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['election-compound-districts-map']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-compound-districts-map class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'embed': False,
            'election_compound': model,
        }


@ElectionDayApp.screen_widget(
    tag='election-compound-superregions-table',
    category='election_compound'
)
class ElectionCompoundSuperregionsTableWidget(ElectionCompoundWidget):
    tag = 'election-compound-superregions-table'
    template = """
        <xsl:template match="election-compound-superregions-table">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['election-compound-superregions-table']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-compound-superregions-table class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        superregions = get_superregions(model, layout.app.principal)
        return {
            'election_compound': model,
            'superregions': superregions
        }


@ElectionDayApp.screen_widget(
    tag='election-compound-superregions-map',
    category='election_compound'
)
class ElectionCompoundSuperregionsMapWidget(ElectionCompoundWidget):
    tag = 'election-compound-superregions-map'
    template = """
        <xsl:template match="election-compound-superregions-map">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['election-compound-superregions-map']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-compound-superregions-map class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'embed': False,
            'election_compound': model,
        }


@ElectionDayApp.screen_widget(
    tag='election-compound-list-groups-chart',
    category='election_compound'
)
class ElectionCompoundListGroupsChartWidget(ChartWidget['ElectionCompound']):
    tag = 'election-compound-list-groups-chart'
    template = """
        <xsl:template match="election-compound-list-groups-chart">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['list-groups-chart']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-compound-list-groups-chart class=""/>'


@ElectionDayApp.screen_widget(
    tag='election-compound-seat-allocation-chart',
    category='election_compound'
)
class ElectionCompoundSeatAllocationChartWidget(
    ChartWidget['ElectionCompound']
):
    tag = 'election-compound-seat-allocation-chart'
    template = """
        <xsl:template match="election-compound-seat-allocation-chart">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['seat-allocation-chart']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-compound-seat-allocation-chart class=""/>'


@ElectionDayApp.screen_widget(
    tag='election-compound-party-strengths-chart',
    category='election_compound'
)
class ElectionCompoundPartyStrengthsChartWidget(
    ChartWidget['ElectionCompound']
):
    tag = 'election-compound-party-strengths-chart'
    template = """
        <xsl:template match="election-compound-party-strengths-chart">
            <div class="{@class}"
                 tal:define="horizontal '{@horizontal}'=='true'">
                <tal:block
                    metal:use-macro="layout.macros['party-strengths-chart']"
                    />
            </div>
        </xsl:template>
    """
    usage = (
        '<election-compound-party-strengths-chart horizontal="false" '
        'class=""/>'
    )
