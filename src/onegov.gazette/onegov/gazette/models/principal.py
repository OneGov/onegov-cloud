from yaml import load


class Principal(object):
    """ The principal is the political entity running the gazette app. """

    def __init__(
        self,
        name='',
        logo='',
        color='',
        on_accept=None,
        time_zone='Europe/Zurich',
        help_link='',
        frontend=False
    ):
        self.name = name
        self.logo = logo
        self.color = color
        self.on_accept = on_accept or {}
        self.time_zone = time_zone
        self.help_link = help_link
        self.frontend = frontend

        assert not self.on_accept or self.on_accept['mail_to']

    @classmethod
    def from_yaml(cls, yaml_source):
        return cls(**load(yaml_source))
