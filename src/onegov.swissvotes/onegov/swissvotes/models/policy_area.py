from cached_property import cached_property
from decimal import Decimal
from onegov.swissvotes import _


class PolicyArea(object):
    """ Helper class for handling of descriptors.

    There are three levels of descriptors, each new level refining the
    given category.

    Policy areas are internally represented as a string value containing the
    descriptor of all three levels seperated by a comma, e.g. "1.12.121".

    Policy areas are stored in the dataset as float, with the pre-decimal part
    refering to the first level category and the decimal part to the category
    of the given level. For example:

        Level 1 descriptor "1": 1
        Level 2 descriptor "1.12": 1.12
        Level 3 descriptor "1.12.121": 1.121

    """

    def __init__(self, value, level=None):
        """ Creates a new policy descriptor out of the given value.

        The given value might be a string (such as "1.12" or "1.12.121"), a
        list (such as [1, 12] or [1, 12, 121]) or a float together with a level
        (such as 1.12/2 or 1.121/3).

        """

        if isinstance(value, str):
            self.value = value
        elif isinstance(value, list):
            self.value = '.'.join([str(x) for x in value])
        elif isinstance(value, Decimal):
            assert level is not None
            self.value = '.'.join(
                str(int(value * 10 ** x)) for x in range(level)
            )
        else:
            raise NotImplementedError()

    def __repr__(self):
        return self.value

    def __eq__(self, other):
        return self.value == other.value

    @cached_property
    def level(self):
        return self.value.count('.') + 1

    @cached_property
    def descriptor(self):
        """ Returns the highest descriptor, e.g. 121 if "1.12.121". """

        return int(self.value.split('.')[-1])

    @cached_property
    def descriptor_path(self):
        """ Returns all descriptors, e.g [1, 12, 12, 121] if "1.12.121". """

        return [int(part) for part in self.value.split('.')]

    @cached_property
    def descriptor_decimal(self):
        """ Returns the descriptor as float for the dataset, e.g 1.121 if
        "1.12.121".

        """

        return Decimal(self.descriptor) / (10 ** (self.level - 1))

    @cached_property
    def label(self):
        """ Returns a translatable label of the highest descriptor, e.g.
        "Bundesverfassung" if "1.12.121".

        """

        return self.label_path[-1]

    @cached_property
    def label_path(self):
        """ Returns translatable labels for all descriptor levels, e.g.
        ["Staatsordnung", "Politisches System", "Bundesverfassung"] if
        "1.12.121".

        """

        result = []
        lookup = PolicyAreaDefinition.all()
        for part in self.descriptor_path:
            lookup = lookup.get(part)
            if not lookup:
                result.append(str(self.descriptor_decimal))
                break
            result.append(lookup.label or str(self.descriptor))
        return result

    def html(self, request):
        title = ' &gt; '.join([
            request.translate(part) for part in self.label_path
        ])
        return f'<span>{title}</span>'


class PolicyAreaDefinition(object):
    """ Helper class for all the policy areas and their translatable labels.

    Example: Get the label of the policy area "1.12.121":

        PolicyAreaDefinition.all().get(1).get(12).get(121).label

    """

    def __init__(self, path=None, label=None, children=None):
        self.path = path or []
        self.decimal = None
        self.value = path[-1] if self.path else None
        self.label = label
        self.children = children or []
        self.index = {
            child.value: index for index, child in enumerate(self.children)
        }

    def get(self, key):
        """ Returns the child with the given value. """
        if key in self.index:
            return self.children[self.index[key]]

    @staticmethod
    def all():
        """ Returns the tree of all policy areas. """

        return PolicyAreaDefinition(children=[
            PolicyAreaDefinition([1], _("d-1-1"), [
                PolicyAreaDefinition([1, 11], _("d-2-11")),
                PolicyAreaDefinition([1, 12], _("d-2-12"), [
                    PolicyAreaDefinition([1, 12, 121], _("d-3-121")),
                    PolicyAreaDefinition([1, 12, 122], _("d-3-122")),
                    PolicyAreaDefinition([1, 12, 123], _("d-3-123")),
                    PolicyAreaDefinition([1, 12, 124], _("d-3-124")),
                ]),
                PolicyAreaDefinition([1, 13], _("d-2-13"), [
                    PolicyAreaDefinition([1, 13, 131], _("d-3-131")),
                    PolicyAreaDefinition([1, 13, 132], _("d-3-132")),
                    PolicyAreaDefinition([1, 13, 133], _("d-3-133")),
                    PolicyAreaDefinition([1, 13, 134], _("d-3-134")),
                ]),
                PolicyAreaDefinition([1, 14], _("d-2-14"), [
                    PolicyAreaDefinition([1, 14, 141], _("d-3-141")),
                    PolicyAreaDefinition([1, 14, 142], _("d-3-142")),
                    PolicyAreaDefinition([1, 14, 143], _("d-3-143")),
                ]),
                PolicyAreaDefinition([1, 15], _("d-2-15"), [
                    PolicyAreaDefinition([1, 15, 151], _("d-3-151")),
                    PolicyAreaDefinition([1, 15, 152], _("d-3-152")),
                    PolicyAreaDefinition([1, 15, 153], _("d-3-153")),
                ]),
                PolicyAreaDefinition([1, 16], _("d-2-16"), [
                    PolicyAreaDefinition([1, 16, 161], _("d-3-161")),
                    PolicyAreaDefinition([1, 16, 162], _("d-3-162")),
                    PolicyAreaDefinition([1, 16, 163], _("d-3-163")),
                    PolicyAreaDefinition([1, 16, 164], _("d-3-164")),
                    PolicyAreaDefinition([1, 16, 165], _("d-3-165")),
                    PolicyAreaDefinition([1, 16, 166], _("d-3-166")),
                ])
            ]),
            PolicyAreaDefinition([2], _("d-1-2"), [
                PolicyAreaDefinition([2, 21], _("d-2-21"), [
                    PolicyAreaDefinition([2, 21, 211], _("d-3-211")),
                    PolicyAreaDefinition([2, 21, 212], _("d-3-212")),
                    PolicyAreaDefinition([2, 21, 213], _("d-3-213")),
                ]),
                PolicyAreaDefinition([2, 22], _("d-2-22"), [
                    PolicyAreaDefinition([2, 22, 221], _("d-3-221")),
                    PolicyAreaDefinition([2, 22, 222], _("d-3-222")),
                    PolicyAreaDefinition([2, 22, 223], _("d-3-223")),
                    PolicyAreaDefinition([2, 22, 224], _("d-3-224")),
                ]),
                PolicyAreaDefinition([2, 23], _("d-2-23"), [
                    PolicyAreaDefinition([2, 23, 231], _("d-3-231")),
                    PolicyAreaDefinition([2, 23, 232], _("d-3-232")),
                ]),
                PolicyAreaDefinition([2, 24], _("d-2-24")),
                PolicyAreaDefinition([2, 25], _("d-2-25")),
                PolicyAreaDefinition([2, 26], _("d-2-26"), [
                    PolicyAreaDefinition([2, 26, 261], _("d-3-261")),
                    PolicyAreaDefinition([2, 26, 262], _("d-3-262")),
                ]),
                PolicyAreaDefinition([2, 27], _("d-2-27")),
                PolicyAreaDefinition([2, 28], _("d-2-28")),
            ]),
            PolicyAreaDefinition([3], _("d-1-3"), [
                PolicyAreaDefinition([3, 31], _("d-2-31"), [
                    PolicyAreaDefinition([3, 31, 311], _("d-3-311")),
                    PolicyAreaDefinition([3, 31, 312], _("d-3-312")),
                    PolicyAreaDefinition([3, 31, 313], _("d-3-313")),
                ]),
                PolicyAreaDefinition([3, 32], _("d-2-32"), [
                    PolicyAreaDefinition([3, 32, 321], _("d-3-321")),
                    PolicyAreaDefinition([3, 32, 322], _("d-3-322")),
                    PolicyAreaDefinition([3, 32, 323], _("d-3-323")),
                    PolicyAreaDefinition([3, 32, 324], _("d-3-324")),
                    PolicyAreaDefinition([3, 32, 325], _("d-3-325")),
                    PolicyAreaDefinition([3, 32, 327], _("d-3-327")),
                    PolicyAreaDefinition([3, 32, 328], _("d-3-328")),
                    PolicyAreaDefinition([3, 32, 329], _("d-3-329")),
                ]),
                PolicyAreaDefinition([3, 33], _("d-2-33")),
            ]),
            PolicyAreaDefinition([4], _("d-1-4"), [
                PolicyAreaDefinition([4, 41], _("d-2-41"), [
                    PolicyAreaDefinition([4, 41, 411], _("d-3-411")),
                    PolicyAreaDefinition([4, 41, 412], _("d-3-412")),
                    PolicyAreaDefinition([4, 41, 413], _("d-3-413")),
                    PolicyAreaDefinition([4, 41, 414], _("d-3-414")),
                    PolicyAreaDefinition([4, 41, 415], _("d-3-415")),
                    PolicyAreaDefinition([4, 41, 416], _("d-3-416")),
                ]),
                PolicyAreaDefinition([4, 42], _("d-2-42"), [
                    PolicyAreaDefinition([4, 42, 421], _("d-3-421")),
                    PolicyAreaDefinition([4, 42, 422], _("d-3-422")),
                    PolicyAreaDefinition([4, 42, 423], _("d-3-423")),
                    PolicyAreaDefinition([4, 42, 424], _("d-3-424")),
                ]),
                PolicyAreaDefinition([4, 43], _("d-2-43"), [
                    PolicyAreaDefinition([4, 43, 431], _("d-3-431")),
                    PolicyAreaDefinition([4, 43, 432], _("d-3-432")),
                ]),
                PolicyAreaDefinition([4, 44], _("d-2-44"), [
                    PolicyAreaDefinition([4, 44, 441], _("d-3-441")),
                    PolicyAreaDefinition([4, 44, 442], _("d-3-442")),
                    PolicyAreaDefinition([4, 44, 443], _("d-3-443")),
                ]),
            ]),
            PolicyAreaDefinition([5], _("d-1-5"), [
                PolicyAreaDefinition([5, 51], _("d-2-51")),
                PolicyAreaDefinition([5, 52], _("d-2-52")),
                PolicyAreaDefinition([5, 53], _("d-2-53")),
                PolicyAreaDefinition([5, 54], _("d-2-54")),
                PolicyAreaDefinition([5, 55], _("d-2-55")),
            ]),
            PolicyAreaDefinition([6], _("d-1-6"), [
                PolicyAreaDefinition([6, 61], _("d-2-61"), [
                    PolicyAreaDefinition([6, 61, 611], _("d-3-611")),
                    PolicyAreaDefinition([6, 61, 612], _("d-3-612")),
                    PolicyAreaDefinition([6, 61, 613], _("d-3-613")),
                    PolicyAreaDefinition([6, 61, 614], _("d-3-614")),
                ]),
                PolicyAreaDefinition([6, 62], _("d-2-62")),
                PolicyAreaDefinition([6, 63], _("d-2-63")),
                PolicyAreaDefinition([6, 64], _("d-2-64")),
            ]),
            PolicyAreaDefinition([7], _("d-1-7"), [
                PolicyAreaDefinition([7, 71], _("d-2-71")),
                PolicyAreaDefinition([7, 72], _("d-2-72")),
                PolicyAreaDefinition([7, 73], _("d-2-73")),
                PolicyAreaDefinition([7, 74], _("d-2-74")),
                PolicyAreaDefinition([7, 75], _("d-2-75")),
            ]),
            PolicyAreaDefinition([8], _("d-1-8"), [
                PolicyAreaDefinition([8, 81], _("d-2-81"), [
                    PolicyAreaDefinition([8, 81, 811], _("d-3-811")),
                    PolicyAreaDefinition([8, 81, 812], _("d-3-812")),
                ]),
                PolicyAreaDefinition([8, 82], _("d-2-82"), [
                    PolicyAreaDefinition([8, 82, 821], _("d-3-821")),
                    PolicyAreaDefinition([8, 82, 822], _("d-3-822")),
                ]),
                PolicyAreaDefinition([8, 83], _("d-2-83"), [
                    PolicyAreaDefinition([8, 83, 831], _("d-3-831")),
                    PolicyAreaDefinition([8, 83, 832], _("d-3-832")),
                ]),
                PolicyAreaDefinition([8, 84], _("d-2-84")),
                PolicyAreaDefinition([8, 85], _("d-2-85")),
                PolicyAreaDefinition([8, 86], _("d-2-86")),
                PolicyAreaDefinition([8, 87], _("d-2-87")),
            ]),
            PolicyAreaDefinition([9], _("d-1-9"), [
                PolicyAreaDefinition([9, 91], _("d-2-91"), [
                    PolicyAreaDefinition([9, 91, 911], _("d-3-911")),
                    PolicyAreaDefinition([9, 91, 912], _("d-3-912")),
                ]),
                PolicyAreaDefinition([9, 92], _("d-2-92"), [
                    PolicyAreaDefinition([9, 92, 921], _("d-3-921")),
                    PolicyAreaDefinition([9, 92, 922], _("d-3-922")),
                ]),
                PolicyAreaDefinition([9, 93], _("d-2-93"), [
                    PolicyAreaDefinition([9, 93, 931], _("d-3-931")),
                    PolicyAreaDefinition([9, 93, 932], _("d-3-932")),
                    PolicyAreaDefinition([9, 93, 933], _("d-3-933")),
                    PolicyAreaDefinition([9, 93, 934], _("d-3-934")),
                    PolicyAreaDefinition([9, 93, 935], _("d-3-935")),
                    PolicyAreaDefinition([9, 93, 936], _("d-3-936")),
                    PolicyAreaDefinition([9, 93, 937], _("d-3-937")),
                    PolicyAreaDefinition([9, 93, 938], _("d-3-938")),
                ]),
            ]),
            PolicyAreaDefinition([10], _("d-1-10"), [
                PolicyAreaDefinition([10, 101], _("d-2-101"), [
                    PolicyAreaDefinition([10, 101, 1011], _("d-3-1011")),
                    PolicyAreaDefinition([10, 101, 1012], _("d-3-1012")),
                    PolicyAreaDefinition([10, 101, 1013], _("d-3-1013")),
                    PolicyAreaDefinition([10, 101, 1014], _("d-3-1014")),
                    PolicyAreaDefinition([10, 101, 1015], _("d-3-1015")),
                ]),
                PolicyAreaDefinition([10, 102], _("d-2-102"), [
                    PolicyAreaDefinition([10, 102, 1021], _("d-3-1021")),
                    PolicyAreaDefinition([10, 102, 1022], _("d-3-1022")),
                    PolicyAreaDefinition([10, 102, 1023], _("d-3-1023")),
                    PolicyAreaDefinition([10, 102, 1024], _("d-3-1024")),
                    PolicyAreaDefinition([10, 102, 1025], _("d-3-1025")),
                    PolicyAreaDefinition([10, 102, 1026], _("d-3-1026")),
                    PolicyAreaDefinition([10, 102, 1027], _("d-3-1027")),
                    PolicyAreaDefinition([10, 102, 1028], _("d-3-1028")),
                ]),
                PolicyAreaDefinition([10, 103], _("d-2-103"), [
                    PolicyAreaDefinition([10, 103, 1031], _("d-3-1031")),
                    PolicyAreaDefinition([10, 103, 1032], _("d-3-1032")),
                    PolicyAreaDefinition([10, 103, 1033], _("d-3-1033")),
                    PolicyAreaDefinition([10, 103, 1034], _("d-3-1034")),
                    PolicyAreaDefinition([10, 103, 1035], _("d-3-1035")),
                    PolicyAreaDefinition([10, 103, 1036], _("d-3-1036")),
                    PolicyAreaDefinition([10, 103, 1037], _("d-3-1037")),
                    PolicyAreaDefinition([10, 103, 1038], _("d-3-1038")),
                ]),
            ]),
            PolicyAreaDefinition([11], _("d-1-11"), [
                PolicyAreaDefinition([11, 111], _("d-2-111")),
                PolicyAreaDefinition([11, 112], _("d-2-112")),
                PolicyAreaDefinition([11, 113], _("d-2-113")),
                PolicyAreaDefinition([11, 114], _("d-2-114"), [
                    PolicyAreaDefinition([11, 114, 1141], _("d-3-1141")),
                    PolicyAreaDefinition([11, 114, 1142], _("d-3-1142")),
                ]),
                PolicyAreaDefinition([11, 115], _("d-2-115")),
            ]),
            PolicyAreaDefinition([12], _("d-1-12"), [
                PolicyAreaDefinition([12, 121], _("d-2-121")),
                PolicyAreaDefinition([12, 122], _("d-2-122")),
                PolicyAreaDefinition([12, 123], _("d-2-123")),
                PolicyAreaDefinition([12, 124], _("d-2-124")),
                PolicyAreaDefinition([12, 125], _("d-2-125"), [
                    PolicyAreaDefinition([12, 125, 1251], _("d-3-1251")),
                    PolicyAreaDefinition([12, 125, 1252], _("d-3-1252")),
                    PolicyAreaDefinition([12, 125, 1253], _("d-3-1253")),
                    PolicyAreaDefinition([12, 125, 1254], _("d-3-1254")),
                ]),
            ])
        ])
