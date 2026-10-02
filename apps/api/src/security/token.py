"""Emissao e validacao de access tokens (JWT)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from domain.exception import AuthenticationError
from domain.schema.token import TokenPayloadSchema, TokenSchema
from infra.config.settings import SecuritySettings


class TokenService:
    """Assina e valida os tokens da aplicacao."""

    def __init__(self, settings: SecuritySettings) -> None:
        self._settings = settings

    def create_access_token(
        self,
        subject: str,
        *,
        scopes: list[str] | None = None,
        expires_delta: timedelta | None = None,
    ) -> TokenSchema:
        """Emite um token para `subject`, valido pelo periodo configurado."""
        issued_at = datetime.now(UTC)
        lifetime = expires_delta or timedelta(minutes=self._settings.access_token_expire_minutes)
        expires_at = issued_at + lifetime

        claims: dict[str, Any] = {
            "sub": subject,
            "iat": issued_at,
            "exp": expires_at,
            "iss": self._settings.issuer,
            "scopes": scopes or [],
        }

        token = jwt.encode(
            claims,
            self._settings.secret_key.get_secret_value(),
            algorithm=self._settings.algorithm,
        )
        return TokenSchema(access_token=token, expires_in=int(lifetime.total_seconds()))

    def decode_access_token(self, token: str) -> TokenPayloadSchema:
        """Valida assinatura, emissor e validade do token.

        Raises:
            AuthenticationError: token expirado, adulterado ou de outro emissor.
        """
        try:
            claims = jwt.decode(
                token,
                self._settings.secret_key.get_secret_value(),
                algorithms=[self._settings.algorithm],
                issuer=self._settings.issuer,
                options={"require": ["exp", "iat", "sub"]},
            )
        except jwt.ExpiredSignatureError as error:
            raise AuthenticationError("Token expirado.") from error
        except jwt.InvalidTokenError as error:
            # Mensagem generica de proposito: detalhar o motivo ajuda quem
            # esta tentando forjar um token.
            raise AuthenticationError("Token invalido.") from error

        return TokenPayloadSchema.model_validate(claims)
