from onegov.feriennet import FeriennetApp, _


@FeriennetApp.homepage_widget(tag='registration')
class RegistrationWidget(object):
    template = """
        <xsl:template match="registration">
            <div>
                <a href="./auth/register" class="button">
                    ${register_text}
                </a>
                <a href="./auth/login" class="button secondary">
                    ${login_text}
                </a>
            </div>
        </xsl:template>
    """

    def get_variables(self, layout):
        return {
            'register_text': _("Register a new account"),
            'login_text': _("Go to Login")
        }
