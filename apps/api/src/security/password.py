"""Hashing de senhas.

Argon2id e o algoritmo recomendado pelo OWASP: memoria-intensivo, o que torna
ataque com GPU caro. O hash ja embute o sal e os parametros de custo, entao nao
ha nada a guardar alem da propria string.
"""

from __future__ import annotations

from pwdlib import PasswordHash

# `recommended()` acompanha os parametros de custo recomendados da biblioteca,
# em vez de congelar numeros que envelhecem.
_password_hash = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    """Devolve o hash Argon2id da senha."""
    return _password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara senha e hash em tempo constante.

    Devolve `False` para hash malformado em vez de levantar excecao: um registro
    corrompido nao deve virar erro 500 na rota de login.
    """
    try:
        return _password_hash.verify(plain_password, hashed_password)
    except Exception:  # noqa: BLE001 - hash invalido e apenas falha de autenticacao
        return False


def needs_rehash(hashed_password: str) -> bool:
    """`True` se o hash usa parametros defasados.

    Chamado apos um login bem-sucedido para reescrever o hash com o custo atual,
    sem exigir que o usuario troque a senha.
    """
    return _password_hash.verify_and_update("", hashed_password)[1] is not None
