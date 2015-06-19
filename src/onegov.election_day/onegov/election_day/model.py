import yaml


cantons = {
    'ag', 'ai', 'ar', 'be', 'bl', 'bs', 'fr', 'ge', 'gl', 'ju', 'lu', 'ne',
    'nw', 'ow', 'sg', 'sh', 'so', 'sz', 'tg', 'ti', 'ur', 'vd', 'vs', 'zg',
    'zh'
}


class Principal(object):
    """ The principal is the town or municipality running the election day app.

    """

    def __init__(self, name, logo, canton):
        assert canton in cantons

        self.name = name
        self.logo = logo
        self.canton = canton

    @staticmethod
    def from_yaml(yaml_source):
        return Principal(**yaml.load(yaml_source))
