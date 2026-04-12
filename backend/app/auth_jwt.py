import jwt
from fastapi import Header, HTTPException
from jwt import PyJWKClient
from jwt.exceptions import InvalidIssuerError

from .config import get_settings

_jwks_clients: dict[str, PyJWKClient] = {}


def _jwks_client(jwks_url: str) -> PyJWKClient:
    if jwks_url not in _jwks_clients:
        _jwks_clients[jwks_url] = PyJWKClient(jwks_url, cache_jwk_set=True)
    return _jwks_clients[jwks_url]


def _decode_payload(token: str) -> dict:
    settings = get_settings()
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token header") from e

    alg = (header.get("alg") or "HS256").upper()

    if alg == "HS256":
        secret = settings.supabase_jwt_secret
        if not secret:
            raise HTTPException(
                status_code=500,
                detail="SUPABASE_JWT_SECRET is required for HS256 tokens",
            )
        try:
            return jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        except jwt.PyJWTError as e:
            raise HTTPException(status_code=401, detail=str(e)) from e

    if alg not in ("ES256", "ES384", "RS256", "RS384"):
        raise HTTPException(
            status_code=401,
            detail=f"Unsupported JWT algorithm: {alg}",
        )

    if not settings.supabase_url:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_URL is required to verify ES256/RS256 tokens (JWKS)",
        )

    jwks_url = settings.supabase_url.rstrip("/") + "/auth/v1/.well-known/jwks.json"
    issuer = settings.supabase_url.rstrip("/") + "/auth/v1"
    jwk_client = _jwks_client(jwks_url)
    signing_key = jwk_client.get_signing_key_from_jwt(token)
    key = signing_key.key

    try:
        return jwt.decode(
            token,
            key,
            algorithms=[alg],
            audience="authenticated",
            issuer=issuer,
        )
    except InvalidIssuerError:
        return jwt.decode(
            token,
            key,
            algorithms=[alg],
            audience="authenticated",
        )
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


def user_id_from_authorization(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    payload = _decode_payload(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return str(sub)


def bearer_dep(authorization: str | None = Header(None)) -> str:
    return user_id_from_authorization(authorization)
