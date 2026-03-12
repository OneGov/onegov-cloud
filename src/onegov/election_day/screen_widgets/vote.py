from __future__ import annotations

from onegov.election_day import ElectionDayApp
from onegov.election_day.screen_widgets.generic import ModelBoundWidget


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.layouts import DefaultLayout
    from onegov.election_day.models import ComplexVote  # noqa: F401
    from onegov.election_day.models import Vote  # noqa: F401


@ElectionDayApp.screen_widget(
    tag='vote-counter-proposal-title',
    category='complex_vote'
)
class VoteCounterProposalTitleWidget(ModelBoundWidget['Vote']):
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
class VoteTieBreakerTitleWidget(ModelBoundWidget['ComplexVote']):
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
class VoteProposalResultBarWidget(ModelBoundWidget['Vote']):
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

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'proposal': model.proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-counter-proposal-result-bar',
    category='complex_vote'
)
class VoteCounterProposalResultBarWidget(ModelBoundWidget['ComplexVote']):
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

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'counter_proposal': model.counter_proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-tie-breaker-result-bar',
    category='complex_vote'
)
class VoteTieBreakerResultBarWidget(ModelBoundWidget['ComplexVote']):
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

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'tie_breaker': model.tie_breaker,
        }


@ElectionDayApp.screen_widget(
    tag='vote-proposal-entities-table',
    category='vote'
)
class VoteProposalEntitiesTableWidget(ModelBoundWidget['Vote']):
    tag = 'vote-proposal-entities-table'
    template = """
        <xsl:template match="vote-proposal-entities-table">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-entities-table']"
                    tal:define="ballot proposal;
                                results proposal_results"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-proposal-entities-table class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        ballot = model.proposal
        results = sorted(ballot.results, key=lambda x: x.name)
        return {
            'proposal': ballot,
            'proposal_results': results
        }


@ElectionDayApp.screen_widget(
    tag='vote-counter-proposal-entities-table',
    category='complex_vote'
)
class VoteCounterProposalEntitiesTableWidget(ModelBoundWidget['ComplexVote']):
    tag = 'vote-counter-proposal-entities-table'
    template = """
        <xsl:template match="vote-counter-proposal-entities-table">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-entities-table']"
                    tal:define="ballot counter_proposal;
                                results counter_proposal_results"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-counter-proposal-entities-table class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        ballot = model.counter_proposal
        results = sorted(ballot.results, key=lambda x: x.name)
        return {
            'counter_proposal': ballot,
            'counter_proposal_results': results,
        }


@ElectionDayApp.screen_widget(
    tag='vote-tie-breaker-entities-table',
    category='complex_vote'
)
class VoteTieBreakerEntitiesTableWidget(ModelBoundWidget['ComplexVote']):
    tag = 'vote-tie-breaker-entities-table'
    template = """
        <xsl:template match="vote-tie-breaker-entities-table">
            <div class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['ballot-entities-table']"
                    tal:define="ballot tie_breaker;
                                results tie_breaker_results"
                    />
            </div>
        </xsl:template>
    """
    usage = '<vote-tie-breaker-entities-table class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        ballot = model.tie_breaker
        results = sorted(ballot.results, key=lambda x: x.name)
        return {
            'tie_breaker': ballot,
            'tie_breaker_results': results,
        }


@ElectionDayApp.screen_widget(
    tag='vote-proposal-entities-map',
    category='vote'
)
class VoteProposalEntitiesMap(ModelBoundWidget['Vote']):
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

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'embed': False,
            'proposal': model.proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-counter-proposal-entities-map',
    category='complex_vote'
)
class VoteCounterProposalEntitiesMap(ModelBoundWidget['ComplexVote']):
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

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'embed': False,
            'counter_proposal': model.counter_proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-tie-breaker-entities-map',
    category='complex_vote'
)
class VoteTieBreakerEntitiesMap(ModelBoundWidget['ComplexVote']):
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

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'embed': False,
            'tie_breaker': model.tie_breaker,
        }


@ElectionDayApp.screen_widget(
    tag='vote-proposal-districts-map',
    category='vote'
)
class VoteProposalDistrictsMap(ModelBoundWidget['Vote']):
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

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'embed': False,
            'proposal': model.proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-counter-proposal-districts-map',
    category='complex_vote'
)
class VoteCounterProposalDistrictsMap(ModelBoundWidget['ComplexVote']):
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

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'embed': False,
            'counter_proposal': model.counter_proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-tie-breaker-districts-map',
    category='complex_vote'
)
class VoteTieBreakerDistrictsMap(ModelBoundWidget['ComplexVote']):
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

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'embed': False,
            'tie_breaker': model.tie_breaker,
        }


@ElectionDayApp.screen_widget(
    tag='vote-proposal-turnout',
    category='vote'
)
class VoteProposalTurnoutWidget(ModelBoundWidget['Vote']):
    tag = 'vote-proposal-turnout'
    template = """
        <xsl:template match="vote-proposal-turnout">
            <span class="{@class}">
                ${'{0:.2f}'.format(proposal.turnout)} %
            </span>
        </xsl:template>
    """
    usage = '<vote-proposal-turnout class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'embed': False,
            'proposal': model.proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-counter-proposal-turnout',
    category='complex_vote'
)
class VoteCounterProposalTurnoutWidget(ModelBoundWidget['ComplexVote']):
    tag = 'vote-counter-proposal-turnout'
    template = """
        <xsl:template match="vote-counter-proposal-turnout">
            <span class="{@class}">
                ${'{0:.2f}'.format(counter_proposal.turnout)} %
            </span>
        </xsl:template>
    """
    usage = '<vote-counter-proposal-turnout class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'embed': False,
            'counter_proposal': model.counter_proposal,
        }


@ElectionDayApp.screen_widget(
    tag='vote-tie-breaker-turnout',
    category='complex_vote'
)
class VoteTieBreakerTurnoutWidget(ModelBoundWidget['ComplexVote']):
    tag = 'vote-tie-breaker-turnout'
    template = """
        <xsl:template match="vote-tie-breaker-turnout">
            <span class="{@class}">
                ${'{0:.2f}'.format(tie_breaker.turnout)} %
            </span>
        </xsl:template>
    """
    usage = '<vote-tie-breaker-turnout class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        return {
            'embed': False,
            'tie_breaker': model.tie_breaker,
        }
