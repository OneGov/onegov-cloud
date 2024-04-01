from onegov.org import OrgApp


from typing import Any


class IntranetApp(OrgApp):

    def configure_organisation(
        self,
        *,
        enable_user_registration: bool = False,
        enable_yubikey: bool = True,
        disable_password_reset: bool = False,
        **cfg: Any
    ) -> None:

        super().configure_organisation(
            enable_user_registration=enable_user_registration,
            enable_yubikey=enable_yubikey,
            disable_password_reset=disable_password_reset,
            **cfg
        )
