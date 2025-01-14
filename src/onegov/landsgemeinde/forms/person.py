from __future__ import annotations

from onegov.org.forms.person import (
    PersonForm as OrgPersonForm)


class PersonForm(OrgPersonForm):

    def on_request(self) -> None:
        self.delete_field('academic_title')
        self.delete_field('email')
        self.delete_field('phone')
        self.delete_field('phone_direct')
        self.delete_field('born')
        self.delete_field('website')
        self.delete_field('website_2')
        self.delete_field('location_address')
        self.delete_field('postal_address')
        self.delete_field('postal_code_city')
