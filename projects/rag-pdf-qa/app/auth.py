from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings
from app.security import SecurityError, decode_access_token
from app.user_store import UserRecord, UserStore, UserStoreError


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    username: str
    role: str


def get_user_store(path: str, database_url: str | None = None) -> UserStore:
    return UserStore(path, database_url=database_url)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    try:
        payload = decode_access_token(credentials.credentials, settings.app_secret_key)
        user_id = str(payload.get("sub") or "")
        if not user_id:
            raise SecurityError("Access token has no subject")
        user = get_user_store(settings.user_store_path, settings.database_url).get_user(user_id)
    except (SecurityError, UserStoreError) as exc:
        raise _unauthorized() from exc

    if user is None:
        raise _unauthorized()
    return _to_authenticated_user(user)


def _to_authenticated_user(user: UserRecord) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=user.user_id,
        username=user.username,
        role=user.role,
    )


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
