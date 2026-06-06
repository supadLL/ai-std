import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any


PASSWORD_HASH_ITERATIONS = 210_000
SECRET_CIPHERTEXT_PREFIX = "enc:v1:"


class SecurityError(RuntimeError):
    pass


def encrypt_secret(value: str | None, secret_key: str) -> str | None:
    if value is None:
        return None
    if not value:
        return ""
    if value.startswith(SECRET_CIPHERTEXT_PREFIX):
        return value
    if not secret_key:
        raise SecurityError("Secret encryption key must not be empty")

    key = _derive_secret_key(secret_key)
    nonce = secrets.token_bytes(16)
    plaintext = value.encode("utf-8")
    keystream = _secret_keystream(key, nonce, len(plaintext))
    ciphertext = bytes(left ^ right for left, right in zip(plaintext, keystream))
    tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
    return (
        f"{SECRET_CIPHERTEXT_PREFIX}"
        f"{_base64url_encode(nonce)}:"
        f"{_base64url_encode(ciphertext)}:"
        f"{_base64url_encode(tag)}"
    )


def decrypt_secret(value: str | None, secret_key: str) -> str | None:
    if value is None:
        return None
    if not value or not value.startswith(SECRET_CIPHERTEXT_PREFIX):
        return value
    if not secret_key:
        raise SecurityError("Secret encryption key must not be empty")

    try:
        nonce_text, ciphertext_text, tag_text = value.removeprefix(SECRET_CIPHERTEXT_PREFIX).split(":", 2)
        nonce = _base64url_decode_bytes(nonce_text)
        ciphertext = _base64url_decode_bytes(ciphertext_text)
        tag = _base64url_decode_bytes(tag_text)
    except (ValueError, TypeError) as exc:
        raise SecurityError("Invalid encrypted secret") from exc

    key = _derive_secret_key(secret_key)
    expected_tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected_tag):
        raise SecurityError("Invalid encrypted secret signature")

    keystream = _secret_keystream(key, nonce, len(ciphertext))
    plaintext = bytes(left ^ right for left, right in zip(ciphertext, keystream))
    try:
        return plaintext.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SecurityError("Invalid encrypted secret payload") from exc


def hash_password(password: str) -> str:
    if not password:
        raise SecurityError("Password must not be empty")
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_HASH_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt, expected_digest = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        ).hex()
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(
    *,
    subject: str,
    username: str,
    role: str,
    secret_key: str,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "username": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = f"{_base64url_json(header)}.{_base64url_json(payload)}"
    signature = _sign(signing_input, secret_key)
    return f"{signing_input}.{signature}"


def decode_access_token(token: str, secret_key: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature = token.split(".", 2)
    except ValueError as exc:
        raise SecurityError("Invalid access token") from exc

    signing_input = f"{header_part}.{payload_part}"
    expected_signature = _sign(signing_input, secret_key)
    if not hmac.compare_digest(signature, expected_signature):
        raise SecurityError("Invalid access token signature")

    try:
        header = _base64url_decode_json(header_part)
        payload = _base64url_decode_json(payload_part)
    except (ValueError, json.JSONDecodeError) as exc:
        raise SecurityError("Invalid access token payload") from exc

    if header.get("alg") != "HS256":
        raise SecurityError("Unsupported access token algorithm")

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(datetime.now(UTC).timestamp()):
        raise SecurityError("Access token expired")
    return payload


def _sign(value: str, secret_key: str) -> str:
    digest = hmac.new(secret_key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).digest()
    return _base64url_encode(digest)


def _base64url_json(value: dict[str, Any]) -> str:
    return _base64url_encode(
        json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode_bytes(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _base64url_decode_json(value: str) -> dict[str, Any]:
    decoded = _base64url_decode_bytes(value)
    data = json.loads(decoded.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JWT part must be a JSON object")
    return data


def _derive_secret_key(secret_key: str) -> bytes:
    return hashlib.sha256(secret_key.encode("utf-8")).digest()


def _secret_keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    blocks = []
    counter = 0
    generated = 0
    while generated < length:
        counter_bytes = counter.to_bytes(8, "big")
        block = hmac.new(key, nonce + counter_bytes, hashlib.sha256).digest()
        blocks.append(block)
        generated += len(block)
        counter += 1
    return b"".join(blocks)[:length]
