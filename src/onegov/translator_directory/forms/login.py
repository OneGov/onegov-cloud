from onegov.user.forms import LoginForm as LoginFormBase


class LoginForm(LoginFormBase):

    @property
    def login_data(self):
        """
        Skips auth providers for school users are just indexed by the LDAP but
        not can bot be logged in to. The are authenticated with the user and
        password in our database, so we pass skip_providers to the login data.
        """
        login_data = super().login_data
        username = self.username.data
        if not username or '@' not in username:
            return login_data
        if username.endswith('@zg.ch'):
            return login_data

        # Make sure the username is lowered
        login_data['username'] = login_data['username'].lower()

        return {
            'skip_providers': True,
            **login_data
        }
