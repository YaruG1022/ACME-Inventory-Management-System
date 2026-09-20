from base64 import b64encode
from io import BytesIO

import pyotp
import qrcode


def provisioning_uri(user):
    return pyotp.TOTP(user.token_2fa).provisioning_uri(user.email, issuer_name="ACME Inventory")


def verify_code(user, code):
    return pyotp.TOTP(user.token_2fa).verify(code or "")


def qr_base64(user):
    image = qrcode.make(provisioning_uri(user))
    output = BytesIO()
    image.save(output, format="PNG")
    return b64encode(output.getvalue()).decode("ascii")
