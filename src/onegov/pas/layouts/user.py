from __future__ import annotations

from onegov.town6.layout import (
    UserManagementLayout as Town6UserManagementLayout
)
from onegov.town6.layout import UserLayout as Town6UserLayout
from onegov.town6.layout import (
    UserGroupCollectionLayout as Town6UserGroupCollectionLayout
)
from onegov.town6.layout import UserGroupLayout as Town6UserGroupLayout
from onegov.pas.layouts.default import DefaultLayout

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.app import PasApp
    from onegov.pas.request import PasRequest


class UserManagementLayout(Town6UserManagementLayout, DefaultLayout):

    app: PasApp
    request: PasRequest


class UserLayout(Town6UserLayout, DefaultLayout):

    app: PasApp
    request: PasRequest


class UserGroupCollectionLayout(Town6UserGroupCollectionLayout, DefaultLayout):

    app: PasApp
    request: PasRequest


class UserGroupLayout(Town6UserGroupLayout, DefaultLayout):

    app: PasApp
    request: PasRequest
