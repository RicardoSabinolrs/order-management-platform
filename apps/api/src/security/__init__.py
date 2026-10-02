"""Seguranca: hashing de senha, emissao de tokens e dependencias de auth."""

from security.dependencies import (
    CurrentSubjectDep,
    TokenPayloadDep,
    get_current_subject,
    get_token_payload,
    require_scopes,
)
from security.password import hash_password, needs_rehash, verify_password
from security.token import TokenService

__all__ = [
    "CurrentSubjectDep",
    "TokenPayloadDep",
    "TokenService",
    "get_current_subject",
    "get_token_payload",
    "hash_password",
    "needs_rehash",
    "require_scopes",
    "verify_password",
]
