"""Password storage (R7)."""

import pytest

from api import ApiClient
from config import UserCredentials
from utils.db_manager import DbManager


@pytest.mark.db
@pytest.mark.req("R7")
@pytest.mark.tc("TC-LOGIN-009")
def test_passwords_are_stored_as_salted_hashes(
    regular_user: UserCredentials,
    same_password_user: UserCredentials,
    db_manager: DbManager,
    api_client: ApiClient,
) -> None:
    assert not db_manager.stores_plain_password(regular_user)
    assert not db_manager.stores_plain_password(same_password_user)
    # Equal passwords, different stored values: the hash is salted.
    assert not db_manager.have_same_stored_password(
        regular_user.username, same_password_user.username
    )

    response = api_client.login(regular_user)

    assert api_client.path_of(response) == "/bugs"
