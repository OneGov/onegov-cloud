from onegov.election_day import ElectionDayApp
from onegov.election_day.screen_widgets.generic import ChartWidget
from onegov.election_day.screen_widgets.generic import ModelBoundWidget
from onegov.election_day.utils.election import get_candidates_results
from onegov.election_day.utils.election import get_candidates_results_by_entity
from onegov.election_day.utils.election import get_list_results
from onegov.election_day.utils.parties import get_party_results
from onegov.election_day.utils.parties import get_party_results_deltas


@ElectionDayApp.screen_widget(
    tag='election-candidates-table',
    category='election'
)
class ElectionCandidatesTableWidget(ModelBoundWidget):
    tag = 'election-candidates-table'
    template = """
        <xsl:template match="election-candidates-table">
            <div class="{@class}" tal:define="lists '{@lists}'">
                <tal:block
                    metal:use-macro="layout.macros['election-candidates-table']"
                    tal:define="show_percentage (model.type != 'proporz')"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-candidates-table class="" lists=","/>'

    def get_variables(self, layout):
        model = self.model or layout.model
        session = layout.request.session
        candidates = get_candidates_results(model, session).all()
        return {
            'election': model,
            'candidates': candidates
        }


@ElectionDayApp.screen_widget(
    tag='election-candidates-by-entity-table',
    category='majorz_election'
)
class ElectionCandidatesByEntityTableWidget(ModelBoundWidget):
    tag = 'election-candidates-by-entity-table'
    template = """
        <xsl:template match="election-candidates-by-entity-table">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['election-candidates-by-entity-table']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-candidates-by-entity-table class=""/>'

    def get_variables(self, layout):
        model = self.model or layout.model
        candidates_by_entites = get_candidates_results_by_entity(
            model, sort_by_votes=True
        )
        return {
            'election': model,
            'candidates_by_entites': candidates_by_entites,
        }


@ElectionDayApp.screen_widget(
    tag='election-lists-table',
    category='proporz_election'
)
class ElectionListsTableWidget(ModelBoundWidget):
    tag = 'election-lists-table'
    template = """
        <xsl:template match="election-lists-table">
            <div class="{@class}" tal:define="names '{@names}'">
                <tal:block
                    metal:use-macro="layout.macros['election-lists-table']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-lists-table class="" names=","/>'

    def get_variables(self, layout):
        model = self.model or layout.model
        lists = get_list_results(model).all()
        return {
            'election': model,
            'lists': lists
        }


@ElectionDayApp.screen_widget(
    tag='election-party-strengths-table',
    category='proporz_election'
)
class ElectionPartyStrengthsTableWidget(ModelBoundWidget):
    tag = 'election-party-strengths-table'
    template = """
        <xsl:template match="election-party-strengths-table">
            <div class="{@class}" tal:define="year '{@year}'">
                <tal:block
                    metal:use-macro="layout.macros['party-strengths-table']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-party-strengths-table year="" class=""/>'

    def get_variables(self, layout):
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
    tag='election-candidates-chart',
    category='election'
)
class ElectionCandidatesChartWidget(ChartWidget):
    tag = 'election-candidates-chart'
    template = """
        <xsl:template match="election-candidates-chart">
            <div class="{@class}"
                 tal:define="limit '0{@limit}';
                             lists '{@lists}';
                             elected '{@elected}';
                             sort_by_lists '{@sort-by-lists}';
                             ">
                <tal:block
                    metal:use-macro="layout.macros['candidates-chart']"
                    />
            </div>
        </xsl:template>
    """
    usage = (
        '<election-candidates-chart limit="" lists="," sort-by-lists=""'
        ' elected="" class=""/>'
    )


@ElectionDayApp.screen_widget(
    tag='election-lists-chart',
    category='proporz_election'
)
class ElectionListsChartWidget(ChartWidget):
    tag = 'election-lists-chart'
    template = """
        <xsl:template match="election-lists-chart">
            <div class="{@class}"
                 tal:define="limit '0{@limit}';
                             names '{@names}';
                             sort_by_names '{@sort-by-names}'
                             ">
                <tal:block
                    metal:use-macro="layout.macros['lists-chart']"
                    />
            </div>
        </xsl:template>
    """
    usage = (
        '<election-lists-chart limit="" names="," sort-by-names=""'
        ' class=""/>'
    )


@ElectionDayApp.screen_widget(
    tag='election-party-strengths-chart',
    category='proporz_election'
)
class ElectionPartyStrengthsChartWidget(ChartWidget):
    tag = 'election-party-strengths-chart'
    template = """
        <xsl:template match="election-party-strengths-chart">
            <div class="{@class}"
                 tal:define="horizontal '{@horizontal}'=='true'">
                <tal:block
                    metal:use-macro="layout.macros['party-strengths-chart']"
                    />
            </div>
        </xsl:template>
    """
    usage = (
        '<election-party-strengths-chart horizontal="false" class=""/>'
    )


@ElectionDayApp.screen_widget(
    tag='allocated-mandates',
    category='election'
)
class AllocatedMandatesWidget(ModelBoundWidget):
    tag = 'allocated-mandates'
    template = """
        <xsl:template match="allocated-mandates">
            <span class="{@class}">
                ${layout.format_number(model.allocated_mandates)}
            </span>
        </xsl:template>
    """
    usage = '<allocated-mandates class=""/>'


@ElectionDayApp.screen_widget(
    tag='number-of-mandates',
    category='election'
)
class NumberOfMandatesWidget(ModelBoundWidget):
    tag = 'number-of-mandates'
    template = """
        <xsl:template match="number-of-mandates">
            <span class="{@class}">
                ${layout.format_number(model.number_of_mandates)}
            </span>
        </xsl:template>
    """
    usage = '<number-of-mandates class=""/>'


@ElectionDayApp.screen_widget(
    tag='mandates',
    category='election'
)
class MandatesWidget(ModelBoundWidget):
    tag = 'mandates'
    template = """
        <xsl:template match="mandates">
            <span class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['progress']"
                    tal:define="progress (model.allocated_mandates,\
                                            model.number_of_mandates)"
                    />
            </span>
        </xsl:template>
    """
    usage = '<mandates class=""/>'


@ElectionDayApp.screen_widget(
    tag='election-turnout',
    category='election'
)
class ElectionTurnoutWidget(ModelBoundWidget):
    tag = 'election-turnout'
    template = """
        <xsl:template match="election-turnout">
            <span class="{@class}">
                ${'{0:.2f}'.format(model.turnout)} %
            </span>
        </xsl:template>
    """
    usage = '<election-turnout class=""/>'


@ElectionDayApp.screen_widget(
    tag='absolute-majority',
    category='majorz_election'
)
class AbsoluteMajorityWidget(ModelBoundWidget):
    tag = 'absolute-majority'
    template = """
        <xsl:template match="absolute-majority">
            <span class="{@class}">
                ${layout.format_number(model.absolute_majority or 0)}
            </span>
        </xsl:template>
    """
    usage = '<absolute-majority class=""/>'


@ElectionDayApp.screen_widget(
    tag='if-absolute-majority',
    category='majorz_election'
)
class IfAbsoluteMajorityWidget(ModelBoundWidget):
    tag = 'if-absolute-majority'
    template = """
        <xsl:template match="if-absolute-majority">
            <tal:block tal:condition="model.majority_type == 'absolute'">
                <xsl:apply-templates select="node()"/>
            </tal:block>
        </xsl:template>
    """
    usage = '<if-absolute-majority></if-absolute-majority>'


@ElectionDayApp.screen_widget(
    tag='if-relative-majority',
    category='majorz_election'
)
class IfRelateMajorityWidget(ModelBoundWidget):
    tag = 'if-relative-majority'
    template = """
        <xsl:template match="if-relative-majority">
            <tal:block tal:condition="model.majority_type == 'relative'">
                <xsl:apply-templates select="node()"/>
            </tal:block>
        </xsl:template>
    """
    usage = '<if-relative-majority></if-relative-majority>'
