"""Animais de fazenda. Cada animal pertence a uma construção (home = id da instância).

Como o vínculo é pelo id, mover ou guardar/recolocar a construção não perde os animais.
"""
import random

from . import data

NOMES = ["Mimosa", "Bolinha", "Pipoca", "Estrela", "Fofinha", "Tico", "Neve", "Mel", "Sol", "Nuvem",
         "Bidu", "Lua", "Cacau", "Pingo", "Dengo", "Faísca"]


def new_animal(aid, tipo, home, rng=random):
    return {"id": aid, "t": tipo, "nome": rng.choice(NOMES), "home": home, "fome": 0, "feliz": 70,
            "saude": 100, "amizade": 0, "prog": 0, "pronto": False, "afago": False}


def housing(state, tipo):
    """Primeira construção compatível com vaga livre (ou None)."""
    predio = data.ANIMALS[tipo]["predio"]
    for inst in state.structs.by_id.values():
        sd = data.STRUCTS[inst["s"]]
        if inst["s"] == predio and tipo in sd.get("aceita", []):
            if sum(1 for a in state.animals if a["home"] == inst["id"]) < sd["capacidade"]:
                return inst
    return None


def of_home(animals, home):
    return [a for a in animals if a["home"] == home]


def racao_id(tipo):
    return "racao_" + tipo


def stock(inst, kind="feno"):
    """Quanto há no cocho: feno (kind="feno") ou ração de um animal (kind="racao_vaca", ...)."""
    if kind == "feno":
        return inst["data"].get("feed", 0)
    return inst["data"].get("racao", {}).get(kind, 0)


def _set_stock(inst, kind, n):
    if kind == "feno":
        inst["data"]["feed"] = n
    else:
        inst["data"].setdefault("racao", {})[kind] = n


def add_feed(state, inst, qty=None, kind="feno"):
    """Transfere feno ou ração do inventário para o cocho da construção. Retorna quanto foi colocado.
    Cada tipo de comida tem o seu próprio espaço (limite feed_max)."""
    sd = data.STRUCTS[inst["s"]]
    space = sd["feed_max"] - stock(inst, kind)
    have = state.inv.count(kind)
    qty = min(space, have) if qty is None else min(qty, space, have)
    if qty <= 0:
        return 0
    state.inv.remove(kind, qty)
    _set_stock(inst, kind, stock(inst, kind) + qty)
    return qty


def sell_value(a):
    """Quanto a loja paga pelo animal: depende de amizade, humor e saúde (filhotes valem metade)."""
    base = data.ANIMALS[a["t"]]["preco"]
    f = 0.4 + 0.4 * a["amizade"] / 1000 + 0.3 * a["feliz"] / 100 + 0.2 * a["saude"] / 100
    if a.get("filhote", 0) > 0:
        f *= 0.5
    return max(1, int(base * f))


def sell(state, animal_id):
    a = next((x for x in state.animals if x["id"] == animal_id), None)
    if a is None:
        return False, "Animal não encontrado."
    price = sell_value(a)
    state.animals.remove(a)
    state.money += price
    state.stats["vendas"] = state.stats.get("vendas", 0) + price
    return True, f"Vendeu {a['nome']} ({data.ANIMALS[a['t']]['nome']}) por ${price}."


def pet_all(animals, home):
    n = 0
    for a in of_home(animals, home):
        if not a["afago"]:
            a["afago"] = True
            a["amizade"] = min(1000, a["amizade"] + 10)
            a["feliz"] = min(100, a["feliz"] + 5)
            n += 1
    return n


def product_quality(a):
    if a["amizade"] >= 600 and a["feliz"] >= 80:
        return 2
    if a["amizade"] >= 250 and a["feliz"] >= 60:
        return 1
    return 0


def collect(state, home):
    """Coleta produtos prontos. Retorna (quantidade, xp). Se o inventário encher, o resto fica pronto."""
    got = xp = 0
    for a in of_home(state.animals, home):
        if not a["pronto"]:
            continue
        prod = data.ANIMALS[a["t"]]["produto"]
        q = product_quality(a)
        if not state.inv.can_add(prod, 1, q):
            continue
        state.inv.add(prod, 1, q)
        a["pronto"] = False
        a["amizade"] = min(1000, a["amizade"] + 3)
        got += 1
        xp += 8
    return got, xp


def end_day(state, rng=random, chance_filhote=0.2):
    """Fome, felicidade, produção diária e nascimentos. Retorna quantos filhotes nasceram."""
    for a in state.animals:
        inst = state.structs.by_id.get(a["home"])
        if inst is None:
            continue
        info = data.ANIMALS[a["t"]]
        rid = racao_id(a["t"])
        fed = stock(inst, "feno") > 0 or stock(inst, rid) > 0
        if stock(inst, rid) > 0:                       # a ração do próprio animal vem primeiro e faz mais bem
            _set_stock(inst, rid, stock(inst, rid) - 1)
            a["fome"] = 0
            a["feliz"] = min(100, a["feliz"] + 6)
            a["saude"] = min(100, a["saude"] + 3)
            a["amizade"] = min(1000, a["amizade"] + 2)
        elif fed:
            inst["data"]["feed"] -= 1
            a["fome"] = 0
            a["feliz"] = min(100, a["feliz"] + 3)
            a["saude"] = min(100, a["saude"] + 2)
        else:
            a["fome"] += 1
            a["feliz"] = max(0, a["feliz"] - 8)
            if a["fome"] >= 3:
                a["saude"] = max(0, a["saude"] - 10)
        if not a["afago"]:
            a["feliz"] = max(0, a["feliz"] - 1)
        a["afago"] = False
        if a.get("filhote", 0) > 0:                   # filhote só cresce: ainda não produz
            a["filhote"] -= 1
            continue
        if fed and a["feliz"] >= 30 and a["saude"] >= 30 and not a["pronto"]:
            a["prog"] += 1
            if a["prog"] >= info["periodo"]:
                a["pronto"] = True
                a["prog"] = 0
    return breed(state, rng, chance_filhote)


def can_breed(a):
    return a.get("filhote", 0) <= 0 and a["amizade"] >= 500 and a["feliz"] >= 80 and a["saude"] >= 70


def breed(state, rng=random, chance=0.2):
    """Se dois adultos da mesma espécie, na mesma construção, têm amizade e bem-estar altos,
    há chance de nascer um filhote (precisa de vaga). Retorna quantos nasceram."""
    born = 0
    for inst in list(state.structs.by_id.values()):
        sd = data.STRUCTS[inst["s"]]
        if "capacidade" not in sd:
            continue
        mine = of_home(state.animals, inst["id"])
        for tipo in sd.get("aceita", []):
            par = [a for a in mine if a["t"] == tipo and can_breed(a)]
            if len(par) >= 2 and len(of_home(state.animals, inst["id"])) < sd["capacidade"] and rng.random() < chance:
                baby = new_animal(state.next_animal, tipo, inst["id"], rng)
                baby["filhote"] = 3
                baby["feliz"] = 80
                state.next_animal += 1
                state.animals.append(baby)
                born += 1
    return born
