from onegov.election_day import ElectionDayApp
from onegov.election_day.screen_widgets.generic import ModelBoundWidget
from onegov.election_day.utils.election import get_candidates_results
from onegov.election_day.utils.election import get_elected_candidates
from onegov.election_day.utils.election import get_list_results


@ElectionDayApp.screen_widget(
    tag='election-candidates-table',
    category='election'
)
class ElectionCandidatesTableWidget(ModelBoundWidget):
    tag = 'election-candidates-table'
    template = """
        <xsl:template match="election-candidates-table">
            <tal:block
                metal:use-macro="layout.macros['election-candidates-table']"
                />
        </xsl:template>
    """

    def get_variables(self, layout):
        model = self.model or layout.model
        session = layout.request.session
        candidates = get_candidates_results(model, session).all()
        return {
            'election': model,
            'candidates': candidates
        }


@ElectionDayApp.screen_widget(
    tag='election-compound-candidates-table',
    category='election_compound'
)
class ElectionCompoundCandidatesTableWidget(ModelBoundWidget):
    tag = 'election-compound-candidates-table'
    template = """
        <xsl:template match="election-compound-candidates-table">
            <tal:block
                metal:use-macro="layout.macros['election-compound-candidates-table']"
                />
        </xsl:template>
    """

    def get_variables(self, layout):
        model = self.model or layout.model
        request = layout.request
        session = request.session
        districts = {
            election.id: (election.district, request.link(election))
            for election in model.elections
        }
        elected_candidates = get_elected_candidates(model, session).all()
        return {
            'election_compound': model,
            'elected_candidates': elected_candidates,
            'districts': districts,
        }


@ElectionDayApp.screen_widget(
    tag='election-lists-table',
    category='proporz_election'
)
class ElectionListsTableWidget(ModelBoundWidget):
    tag = 'election-lists-table'
    template = """
        <xsl:template match="election-lists-table">
            <tal:block
                metal:use-macro="layout.macros['election-lists-table']"
                />
        </xsl:template>
    """

    def get_variables(self, layout):
        model = self.model or layout.model
        session = layout.request.session
        lists = get_list_results(model, session).all()
        return {
            'election': model,
            'lists': lists
        }


@ElectionDayApp.screen_widget(
    tag='election-compound-lists-table',
    category='election_compound'
)
class ElectionCompoundListsTableWidget(ModelBoundWidget):
    tag = 'election-compound-lists-table'
    template = """
        <xsl:template match="election-compound-lists-table">
            <tal:block
                metal:use-macro="layout.macros['election-compound-lists-table']"
                />
        </xsl:template>
    """

    def get_variables(self, layout):
        model = self.model or layout.model
        session = layout.request.session
        lists = get_list_results(model, session).all()
        return {
            'election': model,
            'lists': lists
        }


@ElectionDayApp.screen_widget(
    tag='election-compound-districts-table',
    category='election_compound'
)
class ElectionCompoundDistrictsTableWidget(ModelBoundWidget):
    tag = 'election-compound-districts-table'
    template = """
        <xsl:template match="election-compound-districts-table">
            <tal:block
                metal:use-macro="layout.macros['election-compound-districts-table']"
                />
        </xsl:template>
    """

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'election_compound': model,
            'lists': get_list_results(model, layout.request.session)
        }


class ChartWidget(ModelBoundWidget):

    def __init__(self, model=None):
        self.model = model

    def get_variables(self, layout):
        return {
            'embed': False,
            'model': self.model or layout.model
        }


@ElectionDayApp.screen_widget(
    tag='election-candidates-chart',
    category='election'
)
class ElectionCandidatesChartWidget(ChartWidget):
    tag = 'election-candidates-chart'
    template = """
        <xsl:template match="election-candidates-chart">
            <tal:block
                metal:use-macro="layout.macros['candidates-chart']"
                />
        </xsl:template>
    """


@ElectionDayApp.screen_widget(
    tag='election-lists-chart',
    category='proporz_election'
)
class ElectionListsChartWidget(ChartWidget):
    tag = 'election-lists-chart'
    template = """
        <xsl:template match="election-lists-chart">
            <tal:block
                metal:use-macro="layout.macros['lists-chart']"
                />
        </xsl:template>
    """


@ElectionDayApp.screen_widget(
    tag='election-compound-lists-chart',
    category='election_compound'
)
class ElectionCompoundListsChartWidget(ChartWidget):
    tag = 'election-compound-lists-chart'
    template = """
        <xsl:template match="election-compound-lists-chart">
            <tal:block
                metal:use-macro="layout.macros['lists-chart']"
                />
        </xsl:template>
    """
