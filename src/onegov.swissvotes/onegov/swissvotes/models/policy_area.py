from cached_property import cached_property
from decimal import Decimal
from onegov.swissvotes import _


POLICY_AREA = {
    1: {
        'label': _("d-1-1"),
        'children': {
            11: {'label': _("d-2-11")},
            12: {
                'label': _("d-2-12"),
                'children': {
                    121: {'label': _("d-3-121")},
                    122: {'label': _("d-3-122")},
                    123: {'label': _("d-3-123")},
                    124: {'label': _("d-3-124")},
                }

            },
            13: {
                'label': _("d-2-13"),
                'children': {
                    131: {'label': _("d-3-131")},
                    132: {'label': _("d-3-132")},
                    133: {'label': _("d-3-133")},
                    134: {'label': _("d-3-134")},
                }
            },
            14: {
                'label': _("d-2-14"),
                'children': {
                    141: {'label': _("d-3-141")},
                    142: {'label': _("d-3-142")},
                    143: {'label': _("d-3-143")},
                }
            },
            15: {
                'label': _("d-2-15"),
                'children': {
                    151: {'label': _("d-3-151")},
                    152: {'label': _("d-3-152")},
                    153: {'label': _("d-3-153")},
                }
            },
            16: {
                'label': _("d-2-16"),
                'children': {
                    161: {'label': _("d-3-161")},
                    162: {'label': _("d-3-162")},
                    163: {'label': _("d-3-163")},
                    164: {'label': _("d-3-164")},
                    165: {'label': _("d-3-165")},
                }
            },
        }
    },
    2: {
        'label': _("d-1-2"),
        'children': {
            21: {
                'label': _("d-2-21"),
                'children': {
                    211: {'label': _("d-3-211")},
                    212: {'label': _("d-3-212")},
                    213: {'label': _("d-3-213")},
                }
            },
            22: {
                'label': _("d-2-22"),
                'children': {
                    221: {'label': _("d-3-221")},
                    222: {'label': _("d-3-222")},
                    223: {'label': _("d-3-223")},
                    224: {'label': _("d-3-224")},
                }
            },
            23: {
                'label': _("d-2-23"),
                'children': {
                    231: {'label': _("d-3-231")},
                    232: {'label': _("d-3-232")},
                }
            },
            24: {'label': _("d-2-24")},
            25: {'label': _("d-2-25")},
            26: {
                'label': _("d-2-26"),
                'children': {
                    261: {'label': _("d-3-261")},
                    262: {'label': _("d-3-262")},
                }
            },
            27: {'label': _("d-2-27")},
            28: {'label': _("d-2-28")},
        }
    },
    3: {
        'label': _("d-1-3"),
        'children': {
            31: {
                'label': _("d-2-31"),
                'children': {
                    311: {'label': _("d-3-311")},
                    312: {'label': _("d-3-312")},
                    313: {'label': _("d-3-313")},
                }
            },
            32: {
                'label': _("d-2-32"),
                'children': {
                    321: {'label': _("d-3-321")},
                    322: {'label': _("d-3-322")},
                    323: {'label': _("d-3-323")},
                    324: {'label': _("d-3-324")},
                    325: {'label': _("d-3-325")},
                    327: {'label': _("d-3-327")},
                    328: {'label': _("d-3-328")},
                    329: {'label': _("d-3-329")},
                }
            },
            33: {'label': _("d-2-33")},
        }
    },
    4: {
        'label': _("d-1-4"),
        'children': {
            41: {
                'label': _("d-2-41"),
                'children': {
                    411: {'label': _("d-3-411")},
                    412: {'label': _("d-3-412")},
                    413: {'label': _("d-3-413")},
                    414: {'label': _("d-3-414")},
                    415: {'label': _("d-3-415")},
                }
            },
            42: {
                'label': _("d-2-42"),
                'children': {
                    421: {'label': _("d-3-421")},
                    422: {'label': _("d-3-422")},
                    423: {'label': _("d-3-423")},
                    424: {'label': _("d-3-424")},
                }
            },
            43: {
                'label': _("d-2-43"),
                'children': {
                    431: {'label': _("d-3-431")},
                    432: {'label': _("d-3-432")},
                }
            },
            44: {
                'label': _("d-2-44"),
                'children': {
                    441: {'label': _("d-3-441")},
                    442: {'label': _("d-3-442")},
                    443: {'label': _("d-3-443")},
                }
            },
        }
    },
    5: {
        'label': _("d-1-5"),
        'children': {
            51: {'label': _("d-2-51")},
            52: {'label': _("d-2-52")},
            53: {'label': _("d-2-53")},
            54: {'label': _("d-2-54")},
            55: {'label': _("d-2-55")},
        }
    },
    6: {
        'label': _("d-1-6"),
        'children': {
            61: {
                'label': _("d-2-61"),
                'children': {
                    611: {'label': _("d-3-611")},
                    612: {'label': _("d-3-612")},
                    613: {'label': _("d-3-613")},
                    614: {'label': _("d-3-614")},
                }
            },
            62: {'label': _("d-2-62")},
            63: {'label': _("d-2-63")},
            64: {'label': _("d-2-64")},
        }
    },
    7: {
        'label': _("d-1-7"),
        'children': {
            71: {'label': _("d-2-71")},
            72: {'label': _("d-2-72")},
            73: {'label': _("d-2-73")},
            74: {'label': _("d-2-74")},
            75: {'label': _("d-2-75")},
        }
    },
    8: {
        'label': _("d-1-8"),
        'children': {
            81: {
                'label': _("d-2-81"),
                'children': {
                    811: {'label': _("d-3-811")},
                    812: {'label': _("d-3-812")},
                }
            },
            82: {
                'label': _("d-2-82"),
                'children': {
                    821: {'label': _("d-3-821")},
                    822: {'label': _("d-3-822")},
                }
            },
            83: {
                'label': _("d-2-83"),
                'children': {
                    831: {'label': _("d-3-831")},
                    832: {'label': _("d-3-832")},

                }
            },
            84: {'label': _("d-2-84")},
            85: {'label': _("d-2-85")},
            86: {'label': _("d-2-86")},
            87: {'label': _("d-2-87")},
        }
    },
    9: {
        'label': _("d-1-9"),
        'children': {
            91: {
                'label': _("d-2-91"),
                'children': {
                    911: {'label': _("d-3-911")},
                    912: {'label': _("d-3-912")},
                }
            },
            92: {
                'label': _("d-2-92"),
                'children': {
                    921: {'label': _("d-3-921")},
                    922: {'label': _("d-3-922")},
                }
            },
            93: {
                'label': _("d-2-93"),
                'children': {
                    931: {'label': _("d-3-931")},
                    932: {'label': _("d-3-932")},
                    933: {'label': _("d-3-933")},
                    934: {'label': _("d-3-934")},
                    935: {'label': _("d-3-935")},
                    936: {'label': _("d-3-936")},
                    937: {'label': _("d-3-937")},
                    938: {'label': _("d-3-938")},
                }
            },
        }
    },
    10: {
        'label': _("d-1-10"),
        'children': {
            101: {
                'label': _("d-2-101"),
                'children': {
                    1011: {'label': _("d-3-1011")},
                    1012: {'label': _("d-3-1012")},
                    1013: {'label': _("d-3-1013")},
                    1014: {'label': _("d-3-1014")},
                    1015: {'label': _("d-3-1015")},
                }
            },
            102: {
                'label': _("d-2-102"),
                'children': {
                    1021: {'label': _("d-3-1021")},
                    1022: {'label': _("d-3-1022")},
                    1023: {'label': _("d-3-1023")},
                    1024: {'label': _("d-3-1024")},
                    1025: {'label': _("d-3-1025")},
                    1026: {'label': _("d-3-1026")},
                    1027: {'label': _("d-3-1027")},
                    1028: {'label': _("d-3-1028")},
                }
            },
            103: {
                'label': _("d-2-103"),
                'children': {
                    1031: {'label': _("d-3-1031")},
                    1032: {'label': _("d-3-1032")},
                    1033: {'label': _("d-3-1033")},
                    1034: {'label': _("d-3-1034")},
                    1035: {'label': _("d-3-1035")},
                    1036: {'label': _("d-3-1036")},
                    1037: {'label': _("d-3-1037")},
                    1038: {'label': _("d-3-1038")},
                }
            },
        }
    },
    11: {
        'label': _("d-1-11"),
        'children': {
            111: {'label': _("d-2-111")},
            112: {'label': _("d-2-112")},
            113: {'label': _("d-2-113")},
            114: {
                'label': _("d-2-114"),
                'children': {
                    1141: {'label': _("d-3-1141")},
                    1142: {'label': _("d-3-1142")},
                }
            },
            115: {'label': _("d-2-115")},
        }
    },
    12: {
        'label': _("d-1-12"),
        'children': {
            121: {'label': _("d-2-121")},
            122: {'label': _("d-2-122")},
            123: {'label': _("d-2-123")},
            124: {'label': _("d-2-124")},
            125: {
                'label': _("d-2-125"),
                'children': {
                    1251: {'label': _("d-3-1251")},
                    1252: {'label': _("d-3-1252")},
                    1253: {'label': _("d-3-1253")},
                    1254: {'label': _("d-3-1254")},
                }
            },
        }
    }
}


class PolicyArea(object):
    """ Helper class for handling of descriptors. """

    def __init__(self, value, level=None):
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

    @cached_property
    def level(self):
        return self.value.count('.') + 1

    @cached_property
    def descriptor(self):
        return int(self.value.split('.')[-1])

    @cached_property
    def descriptor_path(self):
        return [int(part) for part in self.value.split('.')]

    @cached_property
    def descriptor_decimal(self):
        return Decimal(self.descriptor) / (10 ** (self.level - 1))

    @cached_property
    def label(self):
        return self.label_path[-1]

    @cached_property
    def label_path(self):
        result = []
        lookup = POLICY_AREA
        for part in self.descriptor_path:
            lookup = lookup.get(part, {})
            result.append(lookup.get('label', str(self.descriptor)))
            lookup = lookup.get('children', {})
        return result

    def html(self, request, full=False):
        label_path = [request.translate(part) for part in self.label_path]
        title = ' &gt; '.join(label_path)
        return f'<span>{title}' if full else (
            f'<span title="{title}">{label_path[-1]}</span>'
        )
