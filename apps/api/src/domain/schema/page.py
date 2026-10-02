"""Paginacao."""

from __future__ import annotations

from pydantic import Field

from domain.schema.base import BaseSchema

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class PageQuery(BaseSchema):
    """Recorte pedido pelo cliente."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Page[ItemT](BaseSchema):
    """Uma pagina de resultados.

    `total` e o numero de registros que satisfazem o filtro, nao o tamanho de
    `items` - e o que permite ao cliente montar a paginacao.
    """

    items: list[ItemT]
    total: int
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        return max(1, -(-self.total // self.page_size))
