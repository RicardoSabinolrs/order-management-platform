"""Configuracao da aplicacao, carregada do ambiente.

Ponto unico de leitura de variaveis de ambiente. Nenhum outro modulo toca
`os.environ`: isso mantem o comportamento explicito, testavel, e permite que o
mesmo binario rode em local, staging e producao so trocando o ambiente.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# O processo pode ser iniciado da raiz do monorepo ou de apps/api.
_ENV_FILES = (".env", "../../.env", "../.env")

# Valor obvio de desenvolvimento: recusado fora de local/test.
DEV_SECRET_KEY = "dev-secret-key-trocar-em-producao"  # noqa: S105
DEV_OPERATOR_PASSWORD = "demo1234"  # noqa: S105


class Environment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseSettings(BaseSettings):
    """Conexao com o Postgres."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", env_file=_ENV_FILES, extra="ignore")

    user: str = "order_management"
    password: SecretStr = SecretStr("order_management")
    db: str = "order_management"
    host: str = "localhost"
    port: int = 5432

    pool_size: int = 5
    max_overflow: int = 10
    pool_pre_ping: bool = True
    echo: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def dsn(self) -> str:
        """DSN async usado pelo engine do SQLAlchemy."""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}"
        )


class SecuritySettings(BaseSettings):
    """Assinatura e validade dos tokens."""

    model_config = SettingsConfigDict(env_prefix="SECURITY_", env_file=_ENV_FILES, extra="ignore")

    secret_key: SecretStr = SecretStr(DEV_SECRET_KEY)
    algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    access_token_expire_minutes: int = 30
    issuer: str = "order-management-api"

    # Administrador raiz: existe sem estar no banco e cadastra os demais.
    operator_name: str = "Operador"
    operator_email: str = "operador@sabinolabs.dev"
    operator_password: SecretStr = SecretStr(DEV_OPERATOR_PASSWORD)
    # Arquivo estatico servido pelo frontend, no mesmo origin da aplicacao.
    operator_avatar_url: str | None = "/avatars/operador.jpg"


class ObservabilitySettings(BaseSettings):
    """Metricas e identificacao do servico."""

    model_config = SettingsConfigDict(
        env_prefix="OBSERVABILITY_", env_file=_ENV_FILES, extra="ignore"
    )

    metrics_enabled: bool = True
    metrics_path: str = "/metrics"
    service_name: str = "order-management-api"


class Settings(BaseSettings):
    """Configuracao raiz da API."""

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=_ENV_FILES, extra="ignore")

    env: Environment = Environment.LOCAL
    debug: bool = False
    log_level: str = "INFO"
    log_format: Literal["console", "json"] = "console"

    title: str = "Order Management Platform API"
    version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)

    @property
    def is_production(self) -> bool:
        return self.env is Environment.PRODUCTION

    @model_validator(mode="after")
    def _recusa_segredo_de_desenvolvimento(self) -> Self:
        """Impede que a chave de exemplo chegue a um ambiente real.

        Subir com a chave publica do repositorio permitiria a qualquer pessoa
        forjar um token valido. Melhor o processo nem iniciar.
        """
        if self.env in (Environment.LOCAL, Environment.TEST):
            return self
        if self.security.secret_key.get_secret_value() == DEV_SECRET_KEY:
            msg = (
                f"SECURITY_SECRET_KEY nao foi configurada para o ambiente '{self.env}'. "
                "Defina uma chave propria (ex.: openssl rand -hex 32)."
            )
            raise ValueError(msg)
        if self.security.operator_password.get_secret_value() == DEV_OPERATOR_PASSWORD:
            msg = (
                f"SECURITY_OPERATOR_PASSWORD ainda e a senha de demonstracao no "
                f"ambiente '{self.env}'. Defina uma senha propria."
            )
            raise ValueError(msg)
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Configuracao do processo, resolvida uma unica vez."""
    return Settings()
