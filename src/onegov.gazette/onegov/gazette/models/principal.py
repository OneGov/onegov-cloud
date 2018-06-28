from yaml import load


class Principal(object):
    """ The principal is the political entity running the gazette app. """

    CANTONS = {
        'ag', 'ai', 'ar', 'be', 'bl', 'bs', 'fr', 'ge', 'gl', 'gr', 'ju', 'lu',
        'ne', 'nw', 'ow', 'sg', 'sh', 'so', 'sz', 'tg', 'ti', 'ur', 'vd', 'vs',
        'zg', 'zh'
    }

    def __init__(
        self,
        name='',
        logo='',
        color='',
        canton=None,
        on_accept=None,
        time_zone='Europe/Zurich',
        help_link='',
        publishing=False,
        frontend=False,
        sogc_import=None,
        **kwargs
    ):
        assert not canton or canton in self.CANTONS
        assert not on_accept or on_accept['mail_to']
        assert not frontend or (frontend and publishing)
        assert not sogc_import or (
            sogc_import['endpoint'] and
            sogc_import['category'] and
            sogc_import['organization'] and
            canton
        )

        self.canton = canton
        self.name = name
        self.logo = logo
        self.color = color
        self.on_accept = on_accept or {}
        self.time_zone = time_zone
        self.help_link = help_link
        self.publishing = publishing
        self.frontend = frontend
        self.sogc_import = sogc_import or {}
        if self.sogc_import and canton:
            self.sogc_import['canton'] = canton.upper()

    @classmethod
    def from_yaml(cls, yaml_source):
        return cls(**load(yaml_source))
