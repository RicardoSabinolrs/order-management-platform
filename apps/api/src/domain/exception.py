"""Erros da aplicacao.

`DomainError` descreve algo que o negocio proibe; `InfrastructureError`
descreve uma dependencia tecnica que falhou. A camada `api` e a unica que sabe
traduzir cada um deles em codigo HTTP.
"""

from __future__ import annotations

from typing import Any


class ApplicationError(Exception):
    """Raiz de todos os erros tratados da aplicacao."""

    code: str = "application_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code

    def details(self) -> dict[str, Any]:
        """Campos extras publicados no corpo do erro (RFC 9457)."""
        return {}


# ---------------------------------------------------------------------------
# Negocio
# ---------------------------------------------------------------------------
class DomainError(ApplicationError):
    """Falha expressa na linguagem do negocio."""

    code = "domain_error"


class InvariantViolationError(DomainError):
    """Um modelo recusou um estado que violaria suas invariantes."""

    code = "invariant_violation"


class BusinessRuleViolationError(DomainError):
    """Uma regra de negocio explicita bloqueou a operacao."""

    code = "business_rule_violation"


class EntityNotFoundError(DomainError):
    """A entidade referenciada nao existe."""

    code = "entity_not_found"


class ConcurrencyConflictError(DomainError):
    """O registro foi alterado por outra transacao (lock otimista)."""

    code = "concurrency_conflict"


# ---------------------------------------------------------------------------
# Autenticacao e autorizacao
# ---------------------------------------------------------------------------
class AuthenticationError(ApplicationError):
    """Credencial ausente, malformada ou expirada."""

    code = "unauthenticated"


class AuthorizationError(ApplicationError):
    """Credencial valida, mas sem permissao para a operacao."""

    code = "forbidden"


# ---------------------------------------------------------------------------
# Infraestrutura
# ---------------------------------------------------------------------------
class InfrastructureError(ApplicationError):
    """Uma dependencia tecnica falhou."""

    code = "infrastructure_error"


class DependencyUnavailableError(InfrastructureError):
    """Uma dependencia externa nao esta respondendo.

    Carrega o estado de cada dependencia para que o readiness probe e o
    operador vejam exatamente o que caiu.
    """

    code = "dependency_unavailable"

    def __init__(self, message: str, *, dependencies: list[dict[str, Any]]) -> None:
        super().__init__(message)
        self.dependencies = dependencies

    def details(self) -> dict[str, Any]:
        return {"dependencies": self.dependencies}
