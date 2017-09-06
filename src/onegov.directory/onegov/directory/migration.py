class DirectoryMigration(object):
    """ Takes a directory and the structure/configuration it should have in
    the future.

    It then migrates the existing directory entries, if possible.

    """

    def __init__(self, directory, new_structure, new_configuration):
        self.directory = directory
        self.new_structure = new_structure
        self.new_configuration = new_configuration

    @property
    def possible(self):
        if not self.directory.entries:
            return True

        if self.directory.structure == self.new_structure:
            return True

        return False

    def execute(self):
        assert self.possible

        for entry in self.directory.entries:
            self.directory.update(entry, **entry.values)

        self.directory.structure = self.new_structure
        self.directory.configuration = self.new_configuration
