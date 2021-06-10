from morepath.request import Response
from onegov.core.security import Public
from onegov.org import OrgApp
from onegov.qrcode import QrCode


@OrgApp.view(model=QrCode, permission=Public, request_method='GET')
def get_qr_code_from_payload(self, request):
    return Response(
        self.encoded_image,
        content_type=self.content_type,
        content_disposition=f'inline; filename=qrcode.{self.img_format}'
    )
