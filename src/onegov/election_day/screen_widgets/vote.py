from onegov.election_day import ElectionDayApp
from onegov.election_day.screen_widgets.generic import ModelBoundWidget


@ElectionDayApp.screen_widget(
    tag='vote-counter-proposal-title',
    category='complex_vote'
)
class VoteCounterProposalTitleWidget(ModelBoundWidget):
    tag = 'vote-counter-proposal-title'
    template = """
        <xsl:template match="vote-counter-proposal-title">
            <span tal:content="model.counter_proposal.title"></span>
        </xsl:template>
    """


@ElectionDayApp.screen_widget(
    tag='vote-tie-breaker-title',
    category='complex_vote'
)
class VoteTieBreakerTitleWidget(ModelBoundWidget):
    tag = 'vote-tie-breaker-title'
    template = """
        <xsl:template match="vote-tie-breaker-title">
            <span tal:content="model.tie_breaker.title"></span>
        </xsl:template>
    """


@ElectionDayApp.screen_widget(
    tag='vote-proposal-result-bar',
    category='vote'
)
class VoteProposalResultBarWidget(ModelBoundWidget):
    tag = 'vote-proposal-result-bar'
    template = """
        <xsl:template match="vote-proposal-result-bar">
            <tal:block
                metal:use-macro="layout.macros['ballot-result-bar']"
                tal:define="ballot proposal"
                />
        </xsl:template>
    """

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'proposal': model.proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-counter-proposal-result-bar',
    category='complex_vote'
)
class VoteCounterProposalResultBarWidget(ModelBoundWidget):
    tag = 'vote-counter-proposal-result-bar'
    template = """
        <xsl:template match="vote-counter-proposal-result-bar">
            <tal:block
                metal:use-macro="layout.macros['ballot-result-bar']"
                tal:define="ballot counter_proposal"
                />
        </xsl:template>
    """

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'counter_proposal': model.counter_proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-tie-breaker-result-bar',
    category='complex_vote'
)
class VoteTieBreakerResultBarWidget(ModelBoundWidget):
    tag = 'vote-tie-breaker-result-bar'
    template = """
        <xsl:template match="vote-tie-breaker-result-bar">
            <tal:block
                metal:use-macro="layout.macros['ballot-result-bar']"
                tal:define="ballot tie_breaker"
                />
        </xsl:template>
    """

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'tie_breaker': model.tie_breaker,
        }


@ElectionDayApp.screen_widget(
    tag='vote-proposal-entities-table',
    category='vote'
)
class VoteProposalEntitiesTableWidget(ModelBoundWidget):
    tag = 'vote-proposal-entities-table'
    template = """
        <xsl:template match="vote-proposal-entities-table">
            <tal:block
                metal:use-macro="layout.macros['ballot-entities-table']"
                tal:define="ballot proposal"
                />
        </xsl:template>
    """

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'proposal': model.proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-counter-proposal-entities-table',
    category='complex_vote'
)
class VoteCounterProposalEntitiesTableWidget(ModelBoundWidget):
    tag = 'vote-counter-proposal-entities-table'
    template = """
        <xsl:template match="vote-counter-proposal-entities-table">
            <tal:block
                metal:use-macro="layout.macros['ballot-entities-table']"
                tal:define="ballot counter_proposal"
                />
        </xsl:template>
    """

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'counter_proposal': model.counter_proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-tie-breaker-entities-table',
    category='complex_vote'
)
class VoteTieBreakerEntitiesTableWidget(ModelBoundWidget):
    tag = 'vote-tie-breaker-entities-table'
    template = """
        <xsl:template match="vote-tie-breaker-entities-table">
            <tal:block
                metal:use-macro="layout.macros['ballot-entities-table']"
                tal:define="ballot tie_breaker"
                />
        </xsl:template>
    """

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'tie_breaker': model.tie_breaker,
        }
