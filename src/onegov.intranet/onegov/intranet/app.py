from onegov.org import OrgApp


class IntranetApp(OrgApp):
    pass


@IntranetApp.setting(section='org', name='enable_yubikey')
def get_enable_yubikey():
    return True
