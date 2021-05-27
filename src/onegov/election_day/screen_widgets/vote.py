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
            <span
                tal:content="model.counter_proposal.title"
                class="{@class}"
                />
        </xsl:template>
    """
    usage = '<vote-counter-proposal-title class=""/>'


@ElectionDayApp.screen_widget(
    tag='vote-tie-breaker-title',
    category='complex_vote'
)
class VoteTieBreakerTitleWidget(ModelBoundWidget):
    tag = 'vote-tie-breaker-title'
    template = """
        <xsl:template match="vote-tie-breaker-title">
            <span
                tal:content="model.tie_breaker.title"
                class="{@class}"
                />
        </xsl:template>
    """
    usage = '<vote-tie-breaker-title class=""/>'


@ElectionDayApp.screen_widget(
    tag='vote-proposal-result-bar',
    category='vote'
)
class VoteProposalResultBarWidget(ModelBoundWidget):
    tag = 'vote-proposal-result-bar'
    template = """
        <xsl:template match="vote-proposal-result-bar">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-result-bar']"
                    tal:define="ballot proposal"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-proposal-result-bar class=""/>'

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
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-result-bar']"
                    tal:define="ballot counter_proposal"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-counter-proposal-result-bar class=""/>'

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
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-result-bar']"
                    tal:define="ballot tie_breaker"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-tie-breaker-result-bar class=""/>'

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
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-entities-table']"
                    tal:define="ballot proposal"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-proposal-entities-table class=""/>'

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
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-entities-table']"
                    tal:define="ballot counter_proposal"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-counter-proposal-entities-table class=""/>'

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
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-entities-table']"
                    tal:define="ballot tie_breaker"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-tie-breaker-entities-table class=""/>'

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'tie_breaker': model.tie_breaker,
        }


@ElectionDayApp.screen_widget(
    tag='vote-proposal-entities-map',
    category='vote'
)
class VoteProposalEntitiesMap(ModelBoundWidget):
    tag = 'vote-proposal-entities-map'
    template = """
        <xsl:template match="vote-proposal-entities-map">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-entities-map']"
                    tal:define="ballot proposal"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-proposal-entities-map class=""/>'

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'embed': False,
            'proposal': model.proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-counter-proposal-entities-map',
    category='complex_vote'
)
class VoteCounterProposalEntitiesMap(ModelBoundWidget):
    tag = 'vote-counter-proposal-entities-map'
    template = """
        <xsl:template match="vote-counter-proposal-entities-map">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-entities-map']"
                    tal:define="ballot counter_proposal"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-counter-proposal-entities-map class=""/>'

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'embed': False,
            'counter_proposal': model.counter_proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-tie-breaker-entities-map',
    category='complex_vote'
)
class VoteTieBreakerEntitiesMap(ModelBoundWidget):
    tag = 'vote-tie-breaker-entities-map'
    template = """
        <xsl:template match="vote-tie-breaker-entities-map">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-entities-map']"
                    tal:define="ballot tie_breaker"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-tie-breaker-entities-map class=""/>'

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'embed': False,
            'tie_breaker': model.tie_breaker,
        }


@ElectionDayApp.screen_widget(
    tag='vote-proposal-districts-map',
    category='vote'
)
class VoteProposalDistrictsMap(ModelBoundWidget):
    tag = 'vote-proposal-districts-map'
    template = """
        <xsl:template match="vote-proposal-districts-map">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-districts-map']"
                    tal:define="ballot proposal"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-proposal-districts-map class=""/>'

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'embed': False,
            'proposal': model.proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-counter-proposal-districts-map',
    category='complex_vote'
)
class VoteCounterProposalDistrictsMap(ModelBoundWidget):
    tag = 'vote-counter-proposal-districts-map'
    template = """
        <xsl:template match="vote-counter-proposal-districts-map">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-districts-map']"
                    tal:define="ballot counter_proposal"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-counter-proposal-districts-map class=""/>'

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'embed': False,
            'counter_proposal': model.counter_proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-tie-breaker-districts-map',
    category='complex_vote'
)
class VoteTieBreakerDistrictsMap(ModelBoundWidget):
    tag = 'vote-tie-breaker-districts-map'
    template = """
        <xsl:template match="vote-tie-breaker-districts-map">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-districts-map']"
                    tal:define="ballot tie_breaker"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-tie-breaker-districts-map class=""/>'

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'embed': False,
            'tie_breaker': model.tie_breaker,
        }
