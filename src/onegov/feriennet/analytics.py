from __future__ import annotations

from markupsafe import Markup
from onegov.core.analytics import AnalyticsProvider
from onegov.feriennet import _
from onegov.feriennet import FeriennetApp


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest


@FeriennetApp.analytics_provider(
    name='google_analytics',
    title=_('Google Analytics (Global site tag)')
)
class GoogleAnalytics(AnalyticsProvider):
    template = Markup(
        '<script async src="https://www.googletagmanager.com/'
        'gtag/js?id={google_tag_id}"></script>\n'
        '<script nonce="{csp_nonce}">\n'
        '  window.dataLayer = window.dataLayer || [];\n'
        '  function gtag(){{dataLayer.push(arguments);}}\n'
        "  gtag('js', new Date());\n"
        "  gtag('config', '{google_tag_id}');\n"
        '</script>'
    )

    def template_variables(self, request: OrgRequest) -> RenderData | None:
        if google_tag_id := request.app.org.google_tag_id:
            csp = request.content_security_policy
            csp.script_src.add('https://*.googletagmanager.com')
            return {
                'csp_nonce': request.content_security_policy_nonce('script'),
                'google_tag_id': google_tag_id.replace("'", r"\'")
            }
        return None
