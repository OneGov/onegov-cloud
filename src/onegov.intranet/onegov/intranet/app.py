from onegov.org import OrgApp


class IntranetApp(OrgApp):

    #: the version of this application (do not change manually!)
    version = '0.0.3'

    def configure_organisation(self, **cfg):
        cfg.setdefault('enable_user_registration', False)
        cfg.setdefault('enable_yubikey', True)
        super().configure_organisation(**cfg)
