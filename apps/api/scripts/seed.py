"""Popula o banco com um catalogo e pedidos de demonstracao.

    make seed

Util para ver a aplicacao funcionando com dados reais logo depois de subir a
stack. O script e idempotente: rodar duas vezes nao duplica nada.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from domain.exception import ApplicationError
from domain.schema.order import CustomerInput, OrderCancel, OrderCreate, OrderItemInput
from domain.schema.product import ProductCreate
from domain.service.order import OrderService
from domain.service.product import DuplicateSkuError, ProductService
from infra.config.settings import get_settings
from infra.database.session import Database
from infra.database.unit_of_work import SqlAlchemyUnitOfWork

CATALOGO = [
    ("CAF-500", "Cafe torrado e moido 500g", "Blend da casa, torra media", 3290, 120),
    ("CHA-VER-100", "Cha verde folhas 100g", "Colheita de primavera", 2150, 80),
    ("CAN-ARO-01", "Caneca ceramica 350ml", "Esmaltada, apta a lava-loucas", 4900, 45),
    ("FIL-PAP-103", "Filtro de papel n.103 (100un)", "Compativel com coador grande", 1290, 200),
    ("PRE-FRA-600", "Prensa francesa 600ml", "Vidro borossilicato e aco inox", 18990, 18),
    ("MOE-MAN-01", "Moedor manual em aco", "Moagem regulavel em 15 pontos", 24500, 12),
    ("ACU-MAS-500", "Acucar mascavo organico 500g", "Certificado organico", 1890, 60),
]

CLIENTES = [
    ("Marina Duarte", "marina.duarte@exemplo.com"),
    ("Rafael Nogueira", "rafael.nogueira@exemplo.com"),
    ("Comercial Andrade ME", "compras@andrade.com.br"),
    ("Beatriz Lemos", "beatriz.lemos@exemplo.com"),
    ("Distribuidora Vale Verde", "pedidos@valeverde.com.br"),
]

# (indice do cliente, [(indice do produto, quantidade)], acoes)
PEDIDOS = [
    (0, [(0, 4), (3, 2)], ["confirm", "ship", "deliver"]),
    (1, [(4, 1)], ["confirm", "ship"]),
    (2, [(0, 20), (6, 10)], ["confirm"]),
    (3, [(2, 3), (1, 2)], []),
    (4, [(5, 2)], ["cancel"]),
    (0, [(1, 5)], []),
    (1, [(3, 6), (2, 1)], ["confirm"]),
]


async def main() -> None:
    settings = get_settings()
    database = Database(settings.database)

    def unit_of_work() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(database.session_factory)

    products = ProductService(unit_of_work)
    orders = OrderService(unit_of_work)

    print(f"Semeando {settings.database.host}/{settings.database.db}...")

    criados = []
    for sku, nome, descricao, preco, estoque in CATALOGO:
        try:
            produto = await products.create(
                ProductCreate(
                    sku=sku,
                    name=nome,
                    description=descricao,
                    price_in_cents=preco,
                    initial_stock=estoque,
                )
            )
            print(f"  produto  {sku:<14} {estoque:>4} un.")
        except DuplicateSkuError:
            # Idempotencia: o catalogo ja existe de uma execucao anterior.
            async with unit_of_work() as uow:
                existente = await uow.products.get_by_sku(sku)
            if existente is None:  # pragma: no cover - so ocorre em corrida
                raise
            produto = await products.get(existente.id)
            print(f"  produto  {sku:<14} (ja existia)")
        criados.append(produto)

    for cliente_idx, linhas, acoes in PEDIDOS:
        nome, email = CLIENTES[cliente_idx]
        try:
            pedido = await orders.create(
                OrderCreate(
                    customer=CustomerInput(name=nome, email=email),
                    items=[
                        OrderItemInput(product_id=criados[produto_idx].id, quantity=quantidade)
                        for produto_idx, quantidade in linhas
                    ],
                )
            )
        except ApplicationError as error:
            print(f"  pedido   ignorado: {error.message}")
            continue

        for acao in acoes:
            if acao == "cancel":
                await orders.cancel(pedido.id, OrderCancel(reason="Cliente desistiu da compra"))
            else:
                await getattr(orders, acao)(pedido.id)

        estado = acoes[-1] if acoes else "pending"
        print(f"  pedido   {pedido.reference:<14} {nome} ({estado})")

    await database.dispose()
    print("\nPronto. Abra http://localhost:5173 para ver os dados na interface.")


if __name__ == "__main__":
    asyncio.run(main())
