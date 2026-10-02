"""Consolidacao do painel de controle."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from domain.model.order import OrderStatus
from domain.repository.base import UnitOfWork
from domain.repository.order import DailyOrders
from domain.schema.dashboard import DailyPoint, DashboardRead, LowStockItem, StatusCount
from domain.schema.order import OrderSummary

# Limiar do alerta de reposicao e quantos itens listar no painel.
LOW_STOCK_THRESHOLD = 10
LOW_STOCK_LIMIT = 8
RECENT_ORDERS_LIMIT = 5
TREND_DAYS = 14

OPEN_STATUSES = (OrderStatus.PENDING, OrderStatus.CONFIRMED)


class DashboardService:
    """Monta a visao consolidada de pedidos e estoque.

    Tudo em uma unica transacao: os numeros exibidos lado a lado sao do mesmo
    instante, e nao de leituras que se contradizem.
    """

    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work_factory

    async def overview(self) -> DashboardRead:
        async with self._unit_of_work() as uow:
            orders = await uow.orders.statistics()
            recent = await uow.orders.recent(RECENT_ORDERS_LIMIT)
            products_total, products_active = await uow.products.counts()
            stock = await uow.stock.overview()
            low_stock = await uow.stock.low_stock(
                threshold=LOW_STOCK_THRESHOLD, limit=LOW_STOCK_LIMIT
            )
            daily = await uow.orders.daily_totals(days=TREND_DAYS)

        billable = orders.total - orders.by_status.get(OrderStatus.CANCELLED, 0)

        return DashboardRead(
            orders_total=orders.total,
            orders_open=sum(orders.by_status.get(status, 0) for status in OPEN_STATUSES),
            orders_by_status=[
                StatusCount(status=status, count=orders.by_status.get(status, 0))
                for status in OrderStatus
            ],
            revenue_in_cents=orders.revenue_in_cents,
            # Divisao protegida: sem pedidos faturaveis o ticket medio e zero,
            # nao um erro.
            average_ticket_in_cents=(orders.revenue_in_cents // billable if billable > 0 else 0),
            products_total=products_total,
            products_active=products_active,
            units_on_hand=stock.units_on_hand,
            units_reserved=stock.units_reserved,
            out_of_stock=stock.out_of_stock,
            low_stock=[
                LowStockItem(
                    product_id=str(item.product_id),
                    sku=item.sku,
                    quantity_available=item.quantity_available,
                    quantity_reserved=item.quantity_reserved,
                )
                for item in low_stock
            ],
            daily=self._fill_gaps(daily),
            recent_orders=[OrderSummary.from_domain(order) for order in recent],
        )

    @staticmethod
    def _fill_gaps(daily: list[DailyOrders]) -> list[DailyPoint]:
        """Completa a serie com zeros nos dias sem pedido.

        Um grafico de tempo com dias faltando desenha uma linha que pula o
        vazio e sugere continuidade onde nao houve movimento.
        """
        por_dia = {registro.day: registro for registro in daily}
        hoje = datetime.now(UTC).date()

        pontos: list[DailyPoint] = []
        for offset in range(TREND_DAYS - 1, -1, -1):
            dia = hoje - timedelta(days=offset)
            registro = por_dia.get(dia)
            pontos.append(
                DailyPoint(
                    date=dia,
                    orders=registro.orders if registro else 0,
                    revenue_in_cents=registro.revenue_in_cents if registro else 0,
                )
            )
        return pontos
