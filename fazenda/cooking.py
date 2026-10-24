"""Cozinha da casa: receitas de data/receitas.json. Lógica pura."""
from . import data


def recipes():
    return list(data.RECEITAS)


def missing(state, rid, lotes=1):
    r = data.RECEITAS[rid]
    return [f"{data.ITEMS[i]['nome']} x{n * lotes - state.inv.count(i)}"
            for i, n in r["ingredientes"].items() if state.inv.count(i) < n * lotes]


def can_cook(state, rid, lotes=1):
    r = data.RECEITAS[rid]
    return not missing(state, rid, lotes) and state.inv.can_add(rid, r["rende"] * lotes)


def cook(state, rid, lotes=1):
    r = data.RECEITAS[rid]
    falta = missing(state, rid, lotes)
    if falta:
        return False, "Faltam: " + ", ".join(falta) + "."
    qtd = r["rende"] * lotes
    if not state.inv.can_add(rid, qtd):
        return False, "Inventário cheio."
    for i, n in r["ingredientes"].items():
        state.inv.remove(i, n * lotes)
    state.inv.add(rid, qtd)
    state.add_xp("agricultura", 2 * lotes)
    return True, f"Cozinhou {qtd}x {data.ITEMS[rid]['nome']}."
