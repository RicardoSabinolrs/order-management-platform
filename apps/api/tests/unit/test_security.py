"""Hashing de senha e ciclo de vida dos tokens."""

from __future__ import annotations

from datetime import timedelta

import pytest

from domain.exception import AuthenticationError
from infra.config.settings import Environment, SecuritySettings, Settings
from security.password import hash_password, verify_password
from security.token import TokenService


@pytest.fixture
def token_service() -> TokenService:
    return TokenService(SecuritySettings(issuer="api-de-teste"))


def test_hash_nao_guarda_a_senha_em_claro() -> None:
    hashed = hash_password("senha-secreta")

    assert "senha-secreta" not in hashed
    assert hashed.startswith("$argon2")


def test_hashes_da_mesma_senha_sao_diferentes() -> None:
    # Sal aleatorio: dois usuarios com a mesma senha nao compartilham hash.
    assert hash_password("mesma-senha") != hash_password("mesma-senha")


def test_verificacao_aceita_a_senha_correta_e_recusa_a_errada() -> None:
    hashed = hash_password("senha-secreta")

    assert verify_password("senha-secreta", hashed) is True
    assert verify_password("senha-errada", hashed) is False


def test_verificacao_de_hash_corrompido_nao_levanta_excecao() -> None:
    assert verify_password("qualquer", "isto-nao-e-um-hash") is False


def test_token_emitido_pode_ser_decodificado(token_service: TokenService) -> None:
    token = token_service.create_access_token("usuario-42", scopes=["orders:read"])

    payload = token_service.decode_access_token(token.access_token)

    assert token.token_type == "bearer"
    assert token.expires_in == 30 * 60
    assert payload.sub == "usuario-42"
    assert payload.scopes == ["orders:read"]


def test_token_expirado_e_recusado(token_service: TokenService) -> None:
    token = token_service.create_access_token("usuario-42", expires_delta=timedelta(seconds=-1))

    with pytest.raises(AuthenticationError, match="expirado"):
        token_service.decode_access_token(token.access_token)


def test_token_assinado_com_outra_chave_e_recusado(token_service: TokenService) -> None:
    outro_servico = TokenService(
        SecuritySettings(
            secret_key="outra-chave-completamente-diferente-e-longa",
            issuer="api-de-teste",
        )
    )
    token = outro_servico.create_access_token("invasor")

    with pytest.raises(AuthenticationError, match="invalido"):
        token_service.decode_access_token(token.access_token)


def test_token_de_outro_emissor_e_recusado(token_service: TokenService) -> None:
    outro_emissor = TokenService(SecuritySettings(issuer="api-estranha"))
    token = outro_emissor.create_access_token("usuario-42")

    with pytest.raises(AuthenticationError, match="invalido"):
        token_service.decode_access_token(token.access_token)


def test_producao_recusa_a_chave_de_desenvolvimento() -> None:
    # Subir em producao com a chave publica do repositorio permitiria forjar
    # qualquer token: o processo precisa falhar no start.
    with pytest.raises(ValueError, match="SECURITY_SECRET_KEY"):
        Settings(env=Environment.PRODUCTION)


def test_producao_recusa_a_senha_de_demonstracao() -> None:
    with pytest.raises(ValueError, match="SECURITY_OPERATOR_PASSWORD"):
        Settings(
            env=Environment.PRODUCTION,
            security=SecuritySettings(secret_key="chave-forte-de-producao-com-tamanho-adequado"),
        )


def test_producao_aceita_configuracao_propria() -> None:
    settings = Settings(
        env=Environment.PRODUCTION,
        security=SecuritySettings(
            secret_key="chave-forte-de-producao-com-tamanho-adequado",
            operator_password="senha-propria-de-producao",
        ),
    )

    assert settings.is_production is True
