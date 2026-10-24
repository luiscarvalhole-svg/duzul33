"""Ferreiro: melhorar ferramentas (madeira -> pedra -> ferro -> ouro) e fundir minérios em barras. Lógica pura."""
from . import data, shops

MAX_NIVEL = 3
BASES = ["picareta", "machado", "enxada", "regador", "espada"]


def find_tool(state, base):
    """Slot do inventário com a ferramenta `base` (de qualquer nível). Retorna (idx, nivel) ou None."""
    for i, sl in enumerate(state.inv.slots):
        if sl:
            it = data.ITEMS[sl["i"]]
            if it["kind"] == "tool" and it["tool"] == base:
                return i, it.get("nivel", 0)
    return None


def cost(state, base):
    """Custo da próxima melhoria: dict {"dinheiro", "materiais"} ou None (sem ferramenta / já no máximo)."""
    f = find_tool(state, base)
    if f is None or f[1] >= MAX_NIVEL:
        return None
    return data.FERREIRO["melhorias"][f[1]]


def missing(state, base):
    c = cost(state, base)
    if c is None:
        return None
    falta = []
    if state.money < c["dinheiro"]:
        falta.append(f"${c['dinheiro'] - state.money}")
    for m, n in c["materiais"].items():
        if state.inv.count(m) < n:
            falta.append(f"{data.ITEMS[m]['nome']} x{n - state.inv.count(m)}")
    return falta


def upgrade(state, base):
    f = find_tool(state, base)
    if f is None:
        return False, "Você não tem essa ferramenta."
    idx, nivel = f
    if nivel >= MAX_NIVEL:
        return False, "Já está no nível máximo."
    falta = missing(state, base)
    if falta:
        return False, "Faltam: " + ", ".join(falta) + "."
    c = data.FERREIRO["melhorias"][nivel]
    state.money -= c["dinheiro"]
    for m, n in c["materiais"].items():
        state.inv.remove(m, n)
    novo = data.tool_id(base, nivel + 1)
    state.inv.slots[idx]["i"] = novo
    return True, f"{data.ITEMS[novo]['nome']} pronta!"


# ----------------------------------------------------------------- fundição
def smelt_missing(state, bar, lotes=1):
    r = data.FERREIRO["fundicao"][bar]
    falta = []
    if state.inv.count(r["minerio"]) < r["n"] * lotes:
        falta.append(f"{data.ITEMS[r['minerio']]['nome']} x{r['n'] * lotes - state.inv.count(r['minerio'])}")
    if state.inv.count("carvao") < r["carvao"] * lotes:
        falta.append(f"Carvão x{r['carvao'] * lotes - state.inv.count('carvao')}")
    return falta


def can_smelt(state, bar, lotes=1):
    return not smelt_missing(state, bar, lotes) and state.inv.can_add(bar, lotes)


def smelt(state, bar, lotes=1):
    falta = smelt_missing(state, bar, lotes)
    if falta:
        return False, "Faltam: " + ", ".join(falta) + "."
    if not state.inv.can_add(bar, lotes):
        return False, "Inventário cheio."
    r = data.FERREIRO["fundicao"][bar]
    state.inv.remove(r["minerio"], r["n"] * lotes)
    state.inv.remove("carvao", r["carvao"] * lotes)
    state.inv.add(bar, lotes)
    state.add_xp("mineracao", 4 * lotes)
    return True, f"Fundiu {lotes}x {data.ITEMS[bar]['nome']}."


def buy_coal(state, n=1):
    price = data.ITEMS["carvao"]["compra"] * n
    if state.money < price:
        return False, "Dinheiro insuficiente."
    if not state.inv.can_add("carvao", n):
        return False, "Inventário cheio."
    state.money -= price
    state.inv.add("carvao", n)
    return True, f"+{n} Carvão (${price})."


def sell_all(state):
    total = shops.sell_all_sellable(state, "ferreiro")
    return (True, f"Vendeu tudo por ${total}.") if total else (False, "Você não tem minérios, barras ou gemas para vender.")


def buy_sword(state):
    if find_tool(state, "espada"):
        return False, "Você já tem uma espada."
    price = data.ITEMS["espada"]["compra"]
    if state.money < price:
        return False, "Dinheiro insuficiente."
    if not state.inv.can_add("espada", 1):
        return False, "Inventário cheio."
    state.money -= price
    state.inv.add("espada", 1)
    return True, "Espada comprada! Use-a na mina."
