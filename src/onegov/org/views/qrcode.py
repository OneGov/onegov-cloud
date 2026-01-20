from __future__ import annotations

from morepath.request import Response
from onegov.core.security import Public
from onegov.org import OrgApp
from onegov.qrcode import QrCode


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest


@OrgApp.view(model=QrCode, permission=Public, request_method='GET')
def get_qr_code_from_payload(self: QrCode, request: OrgRequest) -> Response:
    return Response(
        self.encoded_image,
        content_type=self.content_type,
        content_disposition=f'inline; filename=qrcode.{self.img_format}'
    )
