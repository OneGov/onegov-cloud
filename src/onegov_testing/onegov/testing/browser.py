class ExtendedBrowser(object):
    baseurl = None

    @classmethod
    def leech(cls, obj):
        class LeechedExtendedBrowser(cls, obj.__class__):
            pass

        obj.__class__ = LeechedExtendedBrowser
        return obj

    def visit(self, url):
        if self.baseurl and not url.startswith('http'):
            url = self.baseurl.rstrip('/') + url

        return super().visit(url)

    def login(self, username, password, to=None):
        """ Login a user through the usualy /auth/login path. """

        url = '/auth/login' + (to and ('/?to=' + to) or '')

        self.visit(url)
        self.fill('username', username)
        self.fill('password', password)
        self.find_by_css('form input[type="submit"]').first.click()

    def login_admin(self, to=None):
        self.login('admin@example.org', 'hunter2', to)

    def login_editor(self, to=None):
        self.login('editor@example.org', 'hunter2', to)

    def logout(self):
        self.get('/auth/logout')
