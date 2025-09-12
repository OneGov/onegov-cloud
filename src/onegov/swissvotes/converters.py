from __future__ import annotations
import re

from morepath.converter import Converter


class PolicyAreaListConverter(Converter):

    def verify_format(self, s: str) -> bool:
        # verify is a number or in '1.13.136' format,
        # no alphanumeric character allowed
        return bool(re.fullmatch(r'\d+(\.\d+)*', s))

    def verify_components(self, s: str) -> bool:
        # verify that componenet starts with previous component if
        # split over `.` valid '1.12.123' but invalid '1.22.123'
        components = s.split('.')
        if len(components) == 1:
            return True

        for component in components[1:]:
            if not component.startswith(
                    components[components.index(component) - 1]):
                return False

        return True

    def validate(self, s: str) -> bool:
        if not s:
            return False

        return self.verify_format(s) and self.verify_components(s)

    def decode(self, s: str) -> list[str]:
        if not s:
            return []
        return [item for item in s if self.validate(item)]

    def encode(self, l: list[str]) -> str:
        if not l:
            return []
        return [item for item in l if item]


policy_area_converter = PolicyAreaListConverter(
    decode=PolicyAreaListConverter.decode,
    encode=PolicyAreaListConverter.encode
)
