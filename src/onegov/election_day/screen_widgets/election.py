from onegov.election_day import ElectionDayApp
from onegov.election_day.screen_widgets.generic import ChartWidget
from onegov.election_day.screen_widgets.generic import ModelBoundWidget
from onegov.election_day.utils.election import get_candidates_results
from onegov.election_day.utils.election import get_candidates_results_by_entity
from onegov.election_day.utils.election import get_list_results


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
        candidates_by_entites = get_candidates_results_by_entity(model)
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
                             elected '{@elected}'">
                <tal:block
                    metal:use-macro="layout.macros['candidates-chart']"
                    />
            </div>
        </xsl:template>
    """
    usage = (
        '<election-candidates-chart limit="" lists="," elected="" class=""/>'
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
                 tal:define="limit '0{@limit}'; names '{@names}'"
                 >
                <tal:block
                    metal:use-macro="layout.macros['lists-chart']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-lists-chart limit="" names="," class=""/>'
