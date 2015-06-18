import yaml


class Principal(object):
    """ The principal is the town or municipality running the election day app.

    """

    def __init__(self, name):
        self.name = name

    @staticmethod
    def from_yaml(yaml_source):
        return Principal(**yaml.load(yaml_source))
