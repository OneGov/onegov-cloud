from onegov.org import OrgApp


class WinterthurApp(OrgApp):

    #: the version of this application (do not change manually!)
    version = '0.0.0'

    def configure_organisation(self, **cfg):
        cfg.setdefault('enable_user_registration', False)
        cfg.setdefault('enable_yubikey', False)
        super().configure_organisation(**cfg)
