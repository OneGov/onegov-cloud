from __future__ import annotations

from markupsafe import Markup
from onegov.core.analytics import AnalyticsProvider
from onegov.org import _
from onegov.org import OrgApp
from purl import URL


from typing import Any, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest


@OrgApp.analytics_provider(name='plausible', title=_('Plausible'))
class Plausible(AnalyticsProvider):
    template = Markup(
        '<script defer data-domain="{domain}" src="{script_src}"></script>'
    )

    @property
    def display_name(self) -> str:
        return self.configuration['title'] or self.title

    def url(self, request: OrgRequest) -> str:
        url = URL(self.script_src)
        return url.path(self.domain(request)).as_string()

    @property
    def script_src(self) -> str:
        return self.configuration['script_src']

    def domain(self, request: OrgRequest) -> str:
        return request.app.org.plausible_domain or request.domain

    @classmethod
    def configure(
        cls,
        *,
        script_src: str | None = None,
        title: str | None = None,
        **kwargs: Any
    ) -> Self | None:

        if not script_src:
            return None

        return super().configure(
            script_src=script_src,
            title=title,
        )

    def template_variables(self, request: OrgRequest) -> RenderData:
        request.content_security_policy.script_src.add(self.script_src)
        return {
            'domain': self.domain(request),
            'script_src': self.script_src,
        }


@OrgApp.analytics_provider(name='matomo', title=_('Matomo'))
class Matomo(AnalyticsProvider):
    template = Markup(
        '<script type="text/javascript" nonce="{csp_nonce}">\n'
        'var _paq = window._paq = window._paq || [];\n'
        "_paq.push(['trackPageView']);\n"
        "_paq.push(['enableLinkTracking']);\n"
        '(function() {{ \n'
        '  var u="{matomo_url}";\n'
        "  _paq.push(['setTrackerUrl', u+'piwik.php']);\n"
        "  _paq.push(['setSiteId', '{site_id}']);\n"
        "  var d=document, g=d.createElement('script'), "
            "s=d.getElementsByTagName('script')[0];\n"
        "  g.type='text/javascript'; g.async=true; g.defer=true; "
            "g.src=u+'piwik.js'; s.parentNode.insertBefore(g,s);\n"
        '}})();\n'
        '</script>'
    )

    @property
    def display_name(self) -> str:
        return self.configuration['title'] or self.title

    def url(self, request: OrgRequest) -> str:
        return self.configuration['matomo_url']

    @classmethod
    def configure(
        cls,
        *,
        matomo_url: str | None = None,
        title: str | None = None,
        **kwargs: Any
    ) -> Self | None:

        if not matomo_url:
            return None

        return super().configure(
            matomo_url=matomo_url,
            title=title,
        )

    def template_variables(self, request: OrgRequest) -> RenderData | None:
        if isinstance(site_id := request.app.org.matomo_site_id, int):
            matomo_url = self.configuration['matomo_url']
            request.content_security_policy.script_src.add(matomo_url)
            request.content_security_policy.connect_src.add(matomo_url)
            return {
                'csp_nonce': request.content_security_policy_nonce('script'),
                'matomo_url': matomo_url,
                'site_id': site_id
            }
        return None


@OrgApp.analytics_provider(name='siteimprove', title=_('Siteimprove'))
class SiteimproveAnalytics(AnalyticsProvider):
    template = Markup('<script async src="{script_src}"></script>')

    def url(self, request: OrgRequest) -> str:
        return 'https://www.siteimprove.com/'

    def template_variables(self, request: OrgRequest) -> RenderData | None:
        if isinstance(site_id := request.app.org.siteimprove_site_id, int):
            script_src = (
                f'https://siteimproveanalytics.com/js/'
                f'siteanalyze_{site_id}.js'
            )
            request.content_security_policy.script_src.add(script_src)
            return {'script_src': script_src}
        return None
