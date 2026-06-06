import pytest

import app.auth as auth
import app.main as main
from app.auth import AuthenticatedUser, get_current_user


@pytest.fixture(autouse=True)
def default_authenticated_user(request):
    if request.node.get_closest_marker("no_auth_override"):
        yield
        main.app.dependency_overrides.pop(get_current_user, None)
        main.app.dependency_overrides.pop(auth.get_settings, None)
        return

    main.app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="test-user",
        username="test",
        role="admin",
    )
    yield
    main.app.dependency_overrides.pop(get_current_user, None)


def pytest_configure(config):
    config.addinivalue_line("markers", "no_auth_override: use real auth dependencies")
