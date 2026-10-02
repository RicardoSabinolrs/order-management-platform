"""Traducao de erros da aplicacao para respostas HTTP.

Unico lugar do projeto que conhece codigo de status. Services levantam erros na
linguagem do problema; a conversao para HTTP acontece aqui, e o corpo segue o
RFC 9457 (`application/problem+json`).
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from domain.exception import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    ConcurrencyConflictError,
    DependencyUnavailableError,
    EntityNotFoundError,
    InfrastructureError,
    InvariantViolationError,
)
from infra.logging.setup import get_logger

PROBLEM_JSON = "application/problem+json"

# Ordem importa: o primeiro tipo compativel vence, entao os mais especificos
# vem antes dos mais genericos.
_STATUS_BY_ERROR: tuple[tuple[type[ApplicationError], HTTPStatus], ...] = (
    (EntityNotFoundError, HTTPStatus.NOT_FOUND),
    (ConcurrencyConflictError, HTTPStatus.CONFLICT),
    (BusinessRuleViolationError, HTTPStatus.CONFLICT),
    (InvariantViolationError, HTTPStatus.UNPROCESSABLE_ENTITY),
    (AuthenticationError, HTTPStatus.UNAUTHORIZED),
    (AuthorizationError, HTTPStatus.FORBIDDEN),
    (DependencyUnavailableError, HTTPStatus.SERVICE_UNAVAILABLE),
    (InfrastructureError, HTTPStatus.BAD_GATEWAY),
)

_logger = get_logger(__name__)


def _status_for(error: ApplicationError) -> HTTPStatus:
    for error_type, status in _STATUS_BY_ERROR:
        if isinstance(error, error_type):
            return status
    return HTTPStatus.BAD_REQUEST


def problem_response(
    *,
    status: HTTPStatus,
    title: str,
    detail: str,
    code: str,
    instance: str,
    extra: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Corpo de erro no formato RFC 9457."""
    body: dict[str, Any] = {
        "type": f"about:blank#{code}",
        "title": title,
        "status": int(status),
        "detail": detail,
        "code": code,
        "instance": instance,
    }
    if extra:
        body.update(extra)
    return JSONResponse(
        status_code=int(status),
        content=body,
        media_type=PROBLEM_JSON,
        headers=headers,
    )


async def application_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Erro previsto: logado como aviso, devolvido com o status correspondente."""
    if not isinstance(exc, ApplicationError):  # pragma: no cover - guarda de tipo
        raise exc

    status = _status_for(exc)
    _logger.warning(
        "application_error",
        code=exc.code,
        detail=exc.message,
        path=request.url.path,
        status=int(status),
    )

    headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, AuthenticationError) else None
    return problem_response(
        status=status,
        title=type(exc).__name__,
        detail=exc.message,
        code=exc.code,
        instance=request.url.path,
        extra=exc.details() or None,
        headers=headers,
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Payload que nao satisfaz o contrato do endpoint."""
    if not isinstance(exc, RequestValidationError):  # pragma: no cover
        raise exc

    return problem_response(
        status=HTTPStatus.UNPROCESSABLE_ENTITY,
        title="Requisicao invalida",
        detail="Os dados enviados nao satisfazem o contrato do endpoint.",
        code="validation_error",
        instance=request.url.path,
        extra={"errors": exc.errors()},
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """404/405 e demais erros levantados pelo proprio Starlette."""
    if not isinstance(exc, HTTPException):  # pragma: no cover
        raise exc

    status = HTTPStatus(exc.status_code)
    return problem_response(
        status=status,
        title=status.phrase,
        detail=str(exc.detail),
        code=status.name.lower(),
        instance=request.url.path,
        headers=dict(exc.headers or {}) or None,
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Falha inesperada: stacktrace no log, mensagem generica para o cliente."""
    _logger.exception("unhandled_error", path=request.url.path, error=type(exc).__name__)
    return problem_response(
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
        title="Erro interno",
        detail="Ocorreu um erro inesperado ao processar a requisicao.",
        code="internal_error",
        instance=request.url.path,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Liga os handlers de erro a aplicacao."""
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
