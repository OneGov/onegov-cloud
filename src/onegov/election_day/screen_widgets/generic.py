from onegov.election_day import ElectionDayApp


@ElectionDayApp.screen_widget(tag='h1', category='generic')
class H1Widget:
    tag = 'h1'
    template = """
        <xsl:template match="h1">
            <h1>
                <xsl:apply-templates select="node()"/>
            </h1>
        </xsl:template>
    """


@ElectionDayApp.screen_widget(tag='h2', category='generic')
class H2Widget:
    tag = 'h2'
    template = """
        <xsl:template match="h2">
            <h2>
                <xsl:apply-templates select="node()"/>
            </h2>
        </xsl:template>
    """


@ElectionDayApp.screen_widget(tag='h3', category='generic')
class H3Widget:
    tag = 'h3'
    template = """
        <xsl:template match="h3">
            <h3>
                <xsl:apply-templates select="node()"/>
            </h3>
        </xsl:template>
    """


@ElectionDayApp.screen_widget(tag='hr', category='generic')
class HRWidget:
    tag = 'hr'
    template = """
        <xsl:template match="hr">
            <hr />
        </xsl:template>
    """


@ElectionDayApp.screen_widget(tag='row', category='generic')
class RowWidget(object):
    tag = 'row'
    template = """
        <xsl:template match="row">
            <div class="row" style="max-width: none">
                <xsl:apply-templates select="node()"/>
            </div>
        </xsl:template>
    """


@ElectionDayApp.screen_widget(tag='column', category='generic')
class ColumnWidget(object):
    tag = 'column'
    template = """
        <xsl:template match="column">
            <div class="small-12 medium-{@span} columns">
                <xsl:apply-templates select="node()"/>
                &#160;
            </div>
        </xsl:template>
    """


class ModelBoundWidget:

    def __init__(self, model=None):
        self.model = model

    def get_variables(self, layout):
        return {
            'model': self.model or layout.model
        }


@ElectionDayApp.screen_widget(tag='title', category='generic')
class TitleWidget(ModelBoundWidget):
    tag = 'title'
    template = """
        <xsl:template match="title">
            <span tal:content="model.title"></span>
        </xsl:template>
    """


@ElectionDayApp.screen_widget(tag='progress', category='generic')
class ProgressWidget(ModelBoundWidget):
    tag = 'progress'
    template = """
        <xsl:template match="progress">
            <tal:block
                metal:use-macro="layout.macros['progress']"
                tal:define="progress model.progress"
                />
        </xsl:template>
    """


@ElectionDayApp.screen_widget(tag='counted-entities', category='generic')
class CountedEntitiesWidget(ModelBoundWidget):
    tag = 'counted-entities'
    template = """
        <xsl:template match="counted-entities">
            <div>${entities}</div>
        </xsl:template>
    """

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'model': model,
            'entities': ', '.join(model.counted_entities)
        }
