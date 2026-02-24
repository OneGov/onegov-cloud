from __future__ import annotations

from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.qrcode import QrCode


from typing import Any
from typing import Generic
from typing import TypeVar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.layouts import DefaultLayout
    from onegov.election_day.models import Election
    from onegov.election_day.models import ElectionCompound
    from onegov.election_day.models import Vote
    from typing import TypeAlias

    Entity: TypeAlias = Election | ElectionCompound | Vote


_E = TypeVar('_E', bound='Entity')


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


@ElectionDayApp.screen_widget(tag='p', category='generic')
class PWidget:
    tag = 'p'
    template = """
        <xsl:template match="p">
            <p class="{@class}">
                <xsl:apply-templates select="node()"/>
            </p>
        </xsl:template>
    """
    usage = '<p class=""></p>'


@ElectionDayApp.screen_widget(tag='hr', category='generic')
class HRWidget:
    tag = 'hr'
    template = """
        <xsl:template match="hr">
            <hr class="{@class}" />
        </xsl:template>
    """
    usage = '<hr class=""/>'


@ElectionDayApp.screen_widget(tag='grid-row', category='generic')
class GridRowWidget:
    tag = 'grid-row'
    template = """
        <xsl:template match="grid-row">
            <div class="row {@class}" style="max-width: none">
                <xsl:apply-templates select="node()"/>
            </div>
        </xsl:template>
    """
    usage = '<grid-row class=""></grid-row>'


@ElectionDayApp.screen_widget(tag='grid-column', category='generic')
class GridColumnWidget:
    tag = 'grid-column'
    template = """
        <xsl:template match="grid-column">
            <div class="small-12 medium-{@span} columns {@class}">
                <xsl:apply-templates select="node()"/>
                &#160;
            </div>
        </xsl:template>
    """
    usage = '<grid-column span="" class=""></grid-column>'


@ElectionDayApp.screen_widget(tag='principal-logo', category='generic')
class PrincipalLogoWidget:
    tag = 'principal-logo'
    template = """
        <xsl:template match="principal-logo">
            <img
                tal:attributes="src logo"
                tal:condition="logo"
                class="{@class}"
                />
        </xsl:template>
    """
    usage = '<principal-logo class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        logo = layout.app.logo
        return {'logo': layout.request.link(logo) if logo else ''}


@ElectionDayApp.screen_widget(tag='qr-code', category='generic')
class QrCodeWidget:
    tag = 'qr-code'
    template = """
        <xsl:template match="qr-code">
            <tal:block tal:define="url '{@url}'; src qr_code(url)">
                <img tal:attributes="src src"
                     class="{@class}"
                     />
            </tal:block>

        </xsl:template>
    """
    usage = '<qr-code class="" url="https://"/>'

    @staticmethod
    def qr_code(url: str) -> str:
        return 'data:image/png;base64,{}'.format(
            QrCode(payload=url, encoding='base64').encoded_image.decode()
        )

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        return {'qr_code': self.qr_code}


class ModelBoundWidget(Generic[_E]):

    def __init__(self, model: _E | None = None) -> None:
        self.model = model

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        return {
            'model': self.model or layout.model
        }


@ElectionDayApp.screen_widget(tag='model-title', category='generic')
class ModelTitleWidget(ModelBoundWidget['Entity']):
    tag = 'model-title'
    template = """
        <xsl:template match="model-title">
            <span tal:content="model.title" class="{@class}" />
        </xsl:template>
    """
    usage = '<model-title class=""/>'


@ElectionDayApp.screen_widget(tag='if-completed', category='generic')
class IfCompletedWidget(ModelBoundWidget['Entity']):
    tag = 'if-completed'
    template = """
        <xsl:template match="if-completed">
            <tal:block tal:condition="model.completed">
                <xsl:apply-templates select="node()"/>
            </tal:block>
        </xsl:template>
    """
    usage = '<if-completed></if-completed>'


@ElectionDayApp.screen_widget(tag='if-not-completed', category='generic')
class IfNotCompletedWidget(ModelBoundWidget['Entity']):
    tag = 'if-not-completed'
    template = """
        <xsl:template match="if-not-completed">
            <tal:block tal:condition="not model.completed">
                <xsl:apply-templates select="node()"/>
            </tal:block>
        </xsl:template>
    """
    usage = '<if-not-completed></if-not-completed>'


@ElectionDayApp.screen_widget(tag='model-progress', category='generic')
class ModelProgressWidget(ModelBoundWidget['Entity']):
    tag = 'model-progress'
    template = """
        <xsl:template match="model-progress">
            <span class="{@class}">
                <tal:block
                    metal:use-macro="layout.macros['progress']"
                    tal:define="progress model.progress"
                    />
            </span>
        </xsl:template>
    """
    usage = '<model-progress class=""/>'


@ElectionDayApp.screen_widget(tag='counted-entities', category='generic')
class CountedEntitiesWidget(ModelBoundWidget['Entity']):
    tag = 'counted-entities'
    template = """
        <xsl:template match="counted-entities">
            <span class="{@class}">${entities}</span>
        </xsl:template>
    """
    usage = '<counted-entities class=""/>'

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        model = self.model or layout.model
        entities = ', '.join([
            entity or layout.request.translate(_('Expats'))
            for entity in model.counted_entities
        ])
        return {
            'model': model,
            'entities': entities
        }


class ChartWidget(ModelBoundWidget[_E]):

    def get_variables(self, layout: DefaultLayout) -> dict[str, Any]:
        return {
            'embed': False,
            'model': self.model or layout.model
        }


@ElectionDayApp.screen_widget(tag='last-result-change', category='generic')
class LastResultChangeWidget(ModelBoundWidget['Entity']):
    tag = 'last-result-change'
    template = """
        <xsl:template match="last-result-change">
            <span class="{@class}">
            ${layout.format_date(layout.last_result_change, 'datetime_long')}
            </span>
        </xsl:template>
    """
    usage = '<last-result-change class=""/>'


@ElectionDayApp.screen_widget(
    tag='number-of-counted-entities',
    category='generic'
)
class NumberOfCountedEntitiesWidget(ModelBoundWidget['Entity']):
    tag = 'number-of-counted-entities'
    template = """
        <xsl:template match="number-of-counted-entities">
            <span class="{@class}">
                ${layout.format_number(model.progress[0])}
            </span>
        </xsl:template>
    """
    usage = '<number-of-counted-entities class=""/>'


@ElectionDayApp.screen_widget(tag='total-entities', category='generic')
class TotalEntitiesWidget(ModelBoundWidget['Entity']):
    tag = 'total-entities'
    template = """
        <xsl:template match="total-entities">
            <span class="{@class}">
                ${layout.format_number(model.progress[1])}
            </span>
        </xsl:template>
    """
    usage = '<total-entities class=""/>'
