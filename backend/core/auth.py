# Load libraries
import base64
import io
from datetime import timedelta

import bcrypt
import jwt
import pyotp
import qrcode

from backend.core.config import settings
from backend.core.utils import utcnow

ALGORITHM = "HS256"


# Hashes a plaintext password using bcrypt
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


# Verifies a plaintext password against a bcrypt hash
def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


# Creates a short-lived JWT access token for the given user
def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "scope": "access",
        "exp": utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": utcnow(),
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


# Creates a temporary token for TOTP verification
def create_temp_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "scope": "totp_verification",
        "exp": utcnow() + timedelta(minutes=5),
        "iat": utcnow(),
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


# Decodes and validates a JWT token
def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


# Generates a random TOTP secret key
def generate_totp_secret() -> str:
    return pyotp.random_base32()


# Verifies a TOTP code against the given secret
def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)

    return totp.verify(code, valid_window=1)


# Generates a provisioning URI for TOTP enrolment
def generate_totp_uri(secret: str, username: str) -> str:
    totp = pyotp.TOTP(secret)

    return totp.provisioning_uri(name=username, issuer_name="BibliothecaFabulae")


# Generates a base64-encoded QR code image from a URI
def generate_qr_base64(uri: str) -> str:
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    return base64.b64encode(buffer.getvalue()).decode()
