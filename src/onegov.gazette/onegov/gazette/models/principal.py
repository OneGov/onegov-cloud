from yaml import load


class Principal(object):
    """ The principal is the political entity running the gazette app. """

    def __init__(
        self,
        name='',
        logo='',
        color='',
        publish_to='',
        publish_from='',
        time_zone='Europe/Zurich',
        help_link='',
        show_archive=False
    ):
        self.name = name
        self.logo = logo
        self.color = color
        self.publish_to = publish_to
        self.publish_from = publish_from
        self.time_zone = time_zone
        self.help_link = help_link
        self.show_archive = show_archive

    @classmethod
    def from_yaml(cls, yaml_source):
        return cls(**load(yaml_source))
