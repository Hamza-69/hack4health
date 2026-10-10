import uuid

import jwt
import pytest
from h4h.tokens import TokenType, verify

from core import tokens


def public_key():
    return jwt.PyJWK(tokens.jwks()["keys"][0]).key


def test_module_verifies_user_token_with_published_key():
    user_id = uuid.uuid4()
    claims = verify(tokens.user_token(user_id, "noop"), public_key(), audience="noop", typ=TokenType.USER)
    assert claims["sub"] == str(user_id)


def test_token_for_one_module_is_rejected_by_another():
    token = tokens.user_token(uuid.uuid4(), "noop")
    with pytest.raises(jwt.InvalidAudienceError):
        verify(token, public_key(), audience="pharmacy", typ=TokenType.USER)


def test_token_type_is_checked():
    token = tokens.admin_token(uuid.uuid4(), "a@b.c", "operator", "noop")
    with pytest.raises(jwt.InvalidTokenError, match="user"):
        verify(token, public_key(), audience="noop", typ=TokenType.USER)


def test_session_token_cannot_act_as_module_token():
    token = tokens.session_token(uuid.uuid4())
    with pytest.raises(jwt.InvalidTokenError):
        tokens.verify_core_token(token, TokenType.MODULE)
