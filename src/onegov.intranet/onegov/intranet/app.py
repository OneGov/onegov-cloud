from onegov.org import OrgApp


class IntranetApp(OrgApp):

    def configure_organisation(self, **cfg):
        cfg.setdefault('enable_user_registration', False)
        cfg.setdefault('enable_yubikey', True)
        super().configure_organisation(**cfg)
