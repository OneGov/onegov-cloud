from onegov.election_day import ElectionDayApp
from onegov.election_day.screen_widgets.generic import ChartWidget
from onegov.election_day.screen_widgets.generic import ModelBoundWidget
from onegov.election_day.utils.election_compound import get_elected_candidates
from onegov.election_day.utils.election_compound import get_list_groups


@ElectionDayApp.screen_widget(
    tag='election-compound-candidates-table',
    category='election_compound'
)
class ElectionCompoundCandidatesTableWidget(ModelBoundWidget):
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

    def get_variables(self, layout):
        model = self.model or layout.model
        request = layout.request
        session = request.session
        districts = {
            election.id: (election.domain_segment, request.link(election))
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
class ElectionCompoundListGroupsTableWidget(ModelBoundWidget):
    tag = 'election-compound-list-groups-table'
    template = """
        <xsl:template match="election-compound-list-groups-table">
            <div class="{@class}" tal:define="names '{@names}'">
                <tal:block
                    metal:use-macro="layout.macros['election-compound-list-groups-table']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-compound-list-groups-table class="" />'

    def get_variables(self, layout):
        model = self.model or layout.model
        groups = get_list_groups(model)
        return {
            'election': model,
            'groups': groups
        }


@ElectionDayApp.screen_widget(
    tag='election-compound-districts-table',
    category='election_compound'
)
class ElectionCompoundDistrictsTableWidget(ModelBoundWidget):
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

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'election_compound': model,
        }


@ElectionDayApp.screen_widget(
    tag='election-compound-list-groups-chart',
    category='election_compound'
)
class ElectionCompoundListGroupsChartWidget(ChartWidget):
    tag = 'election-compound-list-groups-chart'
    template = """
        <xsl:template match="election-compound-list-groups-chart">
            <div class="{@class}"
                 tal:define="limit '0{@limit}'; names '{@names}'"
                 >
                <tal:block
                    metal:use-macro="layout.macros['list-groups-chart']"
                    />
            </div>
        </xsl:template>
    """
    usage = '<election-compound-list-groups-chart class=""/>'
