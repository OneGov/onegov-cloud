from onegov.election_day import ElectionDayApp


@ElectionDayApp.screen_widget(tag='h1', category='generic')
class H1Widget:
    tag = 'h1'
    template = """
        <xsl:template match="h1">
            <h1 class="{@class}">
                <xsl:apply-templates select="node()"/>
            </h1>
        </xsl:template>
    """
    usage = '<h1 class=""></h1>'


@ElectionDayApp.screen_widget(tag='h2', category='generic')
class H2Widget:
    tag = 'h2'
    template = """
        <xsl:template match="h2">
            <h2 class="{@class}">
                <xsl:apply-templates select="node()"/>
            </h2>
        </xsl:template>
    """
    usage = '<h2 class=""></h2>'


@ElectionDayApp.screen_widget(tag='h3', category='generic')
class H3Widget:
    tag = 'h3'
    template = """
        <xsl:template match="h3">
            <h3 class="{@class}">
                <xsl:apply-templates select="node()"/>
            </h3>
        </xsl:template>
    """
    usage = '<h3 class=""></h3>'


@ElectionDayApp.screen_widget(tag='text', category='generic')
class TextWidget:
    tag = 'text'
    template = """
        <xsl:template match="text">
            <p class="{@class}">
                <xsl:apply-templates select="node()"/>
            </p>
        </xsl:template>
    """
    usage = '<text class=""></text>'


@ElectionDayApp.screen_widget(tag='hr', category='generic')
class HRWidget:
    tag = 'hr'
    template = """
        <xsl:template match="hr">
            <hr class="{@class}" />
        </xsl:template>
    """
    usage = '<hr class=""/>'


@ElectionDayApp.screen_widget(tag='row', category='generic')
class RowWidget(object):
    tag = 'row'
    template = """
        <xsl:template match="row">
            <div class="row {@class}" style="max-width: none">
                <xsl:apply-templates select="node()"/>
            </div>
        </xsl:template>
    """
    usage = '<row class=""></row>'


@ElectionDayApp.screen_widget(tag='column', category='generic')
class ColumnWidget(object):
    tag = 'column'
    template = """
        <xsl:template match="column">
            <div class="small-12 medium-{@span} columns {@class}">
                <xsl:apply-templates select="node()"/>
                &#160;
            </div>
        </xsl:template>
    """
    usage = '<column span="" class=""></column>'


@ElectionDayApp.screen_widget(tag='logo', category='generic')
class LogoWidget(object):
    tag = 'logo'
    template = """
        <xsl:template match="logo">
            <img
                tal:attributes="src logo"
                tal:condition="logo"
                class="{@class}"
                />
        </xsl:template>
    """
    usage = '<logo class=""/>'

    def get_variables(self, layout):
        logo = layout.app.logo
        return {'logo': layout.request.link(logo) if logo else ''}


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
            <span tal:content="model.title" class="{@class}" />
        </xsl:template>
    """
    usage = '<title class=""/>'


@ElectionDayApp.screen_widget(tag='progress', category='generic')
class ProgressWidget(ModelBoundWidget):
    tag = 'progress'
    template = """
        <xsl:template match="progress">
            <span class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['progress']"
                    tal:define="progress model.progress"
                    />
            </span>
        </xsl:template>
    """
    usage = '<progress class=""/>'


@ElectionDayApp.screen_widget(tag='counted-entities', category='generic')
class CountedEntitiesWidget(ModelBoundWidget):
    tag = 'counted-entities'
    template = """
        <xsl:template match="counted-entities">
            <span class="{@class}">${entities}</span>
        </xsl:template>
    """
    usage = '<counted-entities class=""/>'

    def get_variables(self, layout):
        model = self.model or layout.model
        return {
            'model': model,
            'entities': ', '.join(model.counted_entities)
        }
