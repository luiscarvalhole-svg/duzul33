"""Barraca de vendas: você expõe produtos e, ao fim do dia, fregueses da vila compram. Lógica pura."""
import random

from . import data
from .config import QUALITY_MULT
from .inventory import Inventory

N_SLOTS = 6
MARKUP = 1.3
KINDS = ("crop", "product", "food", "fish")


def shelf(inst):
    return Inventory.from_list(inst["data"].get("loja", []), size=N_SLOTS)


def _save(inst, box):
    inst["data"]["loja"] = box.to_list()


def price(slot):
    it = data.ITEMS[slot["i"]]
    return int(it.get("venda", 0) * QUALITY_MULT[slot["q"]] * MARKUP)


def can_display(item_id):
    it = data.ITEMS[item_id]
    return it["kind"] in KINDS and it.get("venda", 0) > 0


def is_empty(inst):
    return not any(inst["data"].get("loja", []))


def caixa(inst):
    return int(inst["data"].get("caixa", 0))


def put(state, inst, idx):
    sl = state.inv.slots[idx]
    if not sl:
        return False, "Slot vazio."
    if not can_display(sl["i"]):
        return False, "A barraca só vende colheitas, produtos, comidas e peixes."
    box = shelf(inst)
    if not box.can_add(sl["i"], sl["n"], sl["q"]):
        return False, "Prateleiras cheias."
    box.add(sl["i"], sl["n"], sl["q"])
    state.inv.slots[idx] = None
    _save(inst, box)
    return True, ""


def take(state, inst, i):
    box = shelf(inst)
    sl = box.slots[i] if 0 <= i < N_SLOTS else None
    if not sl:
        return False, "Prateleira vazia."
    if not state.inv.can_add(sl["i"], sl["n"], sl["q"]):
        return False, "Inventário cheio."
    state.inv.add(sl["i"], sl["n"], sl["q"])
    box.slots[i] = None
    _save(inst, box)
    return True, ""


def collect(state, inst):
    n = caixa(inst)
    if n <= 0:
        return False, "O caixa está vazio."
    state.money += n
    state.stats["vendas"] = state.stats.get("vendas", 0) + n
    inst["data"]["caixa"] = 0
    return True, f"Recolheu ${n} do caixa."


def customers(state, rng):
    """Quantidade de fregueses do dia (depende do clima)."""
    base = {"sol": 6, "nublado": 4, "chuva": 1, "tempestade": 0, "neve": 1}.get(state.weather, 4)
    return base + rng.randint(0, 2)


def end_day(state):
    """Roda as vendas de todas as barracas. Retorna (itens vendidos, dinheiro total)."""
    itens = total = 0
    for inst in state.structs.by_id.values():
        if inst["s"] != "barraca":
            continue
        rng = random.Random(state.clock.day * 131 + inst["id"])
        box = shelf(inst)
        for _ in range(customers(state, rng)):
            ocupados = [i for i, sl in enumerate(box.slots) if sl]
            if not ocupados:
                break
            i = rng.choice(ocupados)
            sl = box.slots[i]
            q = min(sl["n"], rng.randint(1, 3))
            ganho = price(sl) * q
            box.remove_from_slot(i, q)
            inst["data"]["caixa"] = caixa(inst) + ganho
            itens += q
            total += ganho
        _save(inst, box)
    return itens, total
