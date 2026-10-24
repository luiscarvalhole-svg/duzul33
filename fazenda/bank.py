"""Banco da vila: guardar dinheiro rende juros por dia. Lógica pura."""
RATE = 0.01
MAX_INTEREST = 150


def deposit(state, n):
    n = min(n, state.money)
    if n <= 0:
        return False, "Você não tem dinheiro para depositar."
    state.money -= n
    state.bank += n
    return True, f"Depositou ${n}."


def withdraw(state, n):
    n = min(n, state.bank)
    if n <= 0:
        return False, "Não há saldo para sacar."
    state.bank -= n
    state.money += n
    return True, f"Sacou ${n}."


def interest(state):
    return min(MAX_INTEREST, int(state.bank * RATE))


def end_day(state):
    j = interest(state)
    state.bank += j
    return j
