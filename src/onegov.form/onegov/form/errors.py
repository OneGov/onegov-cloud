class FormError(Exception):
    pass


class DuplicateLabelError(Exception):

    def __init__(self, label):
        self.label = label

    def __repr__(self):
        return "DuplicateLabelError(label='{}')".format(self.label)
