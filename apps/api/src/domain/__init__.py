"""Camada de dominio: regras de negocio, livre de framework e de infraestrutura.

Nada aqui conhece FastAPI, SQLAlchemy ou HTTP. A dependencia aponta para
dentro: `api` e `infra` dependem de `domain`, nunca o contrario. O linter
reprova o caminho inverso (ver pyproject.toml).
"""
