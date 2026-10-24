"""Fabricação de ração no Misturador: cada animal tem a sua receita (data/racoes.json)."""
from . import animals as an
from . import data


def recipe(tipo):
    r = data.RACOES[tipo]
    return {"item": an.racao_id(tipo), "ingredientes": dict(r["ingredientes"]), "rende": r["rende"]}


def can_craft(state, tipo, lotes=1):
    r = recipe(tipo)
    if any(state.inv.count(i) < n * lotes for i, n in r["ingredientes"].items()):
        return False
    return state.inv.can_add(r["item"], r["rende"] * lotes)


def craft(state, tipo, lotes=1):
    r = recipe(tipo)
    falta = [f"{data.ITEMS[i]['nome']} x{n * lotes - state.inv.count(i)}"
             for i, n in r["ingredientes"].items() if state.inv.count(i) < n * lotes]
    if falta:
        return False, "Faltam: " + ", ".join(falta) + "."
    qtd = r["rende"] * lotes
    if not state.inv.can_add(r["item"], qtd):
        return False, "Inventário cheio."
    for i, n in r["ingredientes"].items():
        state.inv.remove(i, n * lotes)
    state.inv.add(r["item"], qtd)
    state.add_xp("pecuaria", 3 * lotes)
    return True, f"Fabricou {qtd}x {data.ITEMS[r['item']]['nome']}."
