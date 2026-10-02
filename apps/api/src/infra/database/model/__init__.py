"""Tabelas do banco.

Modelo de persistencia e modelo de dominio sao coisas distintas: estas classes
descrevem o schema relacional, e os repositorios fazem a traducao entre os dois.
Manter a separacao e o que impede o ORM de ditar o desenho do dominio.
"""

from infra.database.model.order import OrderItemTable, OrderTable
from infra.database.model.product import ProductTable
from infra.database.model.stock import StockItemTable
from infra.database.model.user import UserTable

__all__ = ["OrderItemTable", "OrderTable", "ProductTable", "StockItemTable", "UserTable"]
