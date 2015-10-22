from collections import OrderedDict
from itertools import groupby
from unidecode import unidecode


class AtoZ(object):

    def __init__(self, request):
        self.request = request

    def sortkey(self, item):
        return unidecode(self.get_title(item)[0].upper())

    def get_items_by_letter(self):
        items_by_letter = OrderedDict()

        for letter, items in groupby(self.get_items(), self.sortkey):
            items_by_letter[unidecode(letter)] = tuple(
                sorted(items, key=lambda i: unidecode(self.get_title(i)))
            )

        return items_by_letter

    def get_title(self, item):
        raise NotImplementedError

    def get_items(self):
        raise NotImplementedError
