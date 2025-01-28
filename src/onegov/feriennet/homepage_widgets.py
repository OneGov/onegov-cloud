from __future__ import annotations

from onegov.feriennet import FeriennetApp, _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.feriennet.layout import DefaultLayout


@FeriennetApp.homepage_widget(tag='registration')
class RegistrationWidget:
    template = """
        <xsl:template match="registration">
            <div tal:condition="not:request.is_logged_in" class="register">
                <a href="./auth/register" class="button">
                    ${register_text}
                </a>
                <a href="./auth/login" class="button secondary">
                    ${login_text}
                </a>
            </div>
            <div tal:condition="request.is_logged_in" class="register">
                <a href="./userprofile" class="button secondary">
                    ${profile_text}
                </a>
            </div>
        </xsl:template>
    """

    def get_variables(self, layout: DefaultLayout) -> RenderData:
        return {
            'register_text': _('Register a new account'),
            'login_text': _('Go to Login'),
            'profile_text': _('Go to Profile')
        }
