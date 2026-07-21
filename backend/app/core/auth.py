import re

from fastapi import Header, HTTPException
import jwt
from jwt import PyJWKClient, PyJWTError

from app.core.config import get_settings
from app.core.secrets import SecretConfigurationError, get_secret


USER_ID_PATTERN = re.compile(r'^[A-Za-z0-9_.@-]{1,64}$')


def validate_user_id(user_id: str) -> str:
    user_id = user_id.strip()
    if not USER_ID_PATTERN.fullmatch(user_id):
        raise HTTPException(status_code=400, detail='Invalid user id')
    return user_id


def get_current_user_id(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> str:
    settings = get_settings()
    if settings.auth_mode == 'local':
        return validate_user_id(x_user_id or settings.default_user_id)
    if settings.auth_mode == 'jwt':
        return validate_user_id(get_jwt_user_id(authorization))
    raise HTTPException(status_code=500, detail='Unsupported auth mode')


def get_jwt_user_id(authorization: str | None) -> str:
    token = parse_bearer_token(authorization)
    settings = get_settings()
    try:
        claims = decode_jwt(token)
    except (PyJWTError, SecretConfigurationError, ValueError) as exc:
        raise HTTPException(status_code=401, detail='Invalid bearer token') from exc

    user_id = claims.get(settings.auth_user_id_claim)
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(status_code=401, detail='Bearer token missing user id claim')
    return user_id


def parse_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail='Missing bearer token')
    scheme, _, token = authorization.partition(' ')
    if scheme.lower() != 'bearer' or not token.strip():
        raise HTTPException(status_code=401, detail='Missing bearer token')
    return token.strip()


def decode_jwt(token: str) -> dict:
    settings = get_settings()
    algorithm = settings.auth_jwt_algorithm
    decode_kwargs = {
        'algorithms': [algorithm],
        'audience': settings.auth_jwt_audience,
        'issuer': settings.auth_jwt_issuer,
        'options': {'require': [settings.auth_user_id_claim]},
    }

    if algorithm.startswith('HS'):
        secret = get_secret(settings, 'auth_jwt_secret')
        if not secret:
            raise SecretConfigurationError('AUTH_JWT_SECRET is required for HMAC JWT auth')
        return jwt.decode(token, secret, **decode_kwargs)

    if not settings.auth_jwt_jwks_url:
        raise SecretConfigurationError('AUTH_JWT_JWKS_URL is required for asymmetric JWT auth')
    signing_key = PyJWKClient(settings.auth_jwt_jwks_url).get_signing_key_from_jwt(token)
    return jwt.decode(token, signing_key.key, **decode_kwargs)
